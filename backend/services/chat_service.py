"""
Orquestador de chat.

`process_chat_message`:
  1. Carga la conversación (la crea si no existe).
  2. Carga el historial reciente (últimos N mensajes).
  3. Construye `AgentNodes`, compila el grafo, ejecuta.
  4. Devuelve un objeto con respuesta, fuentes y conversation_id.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.graph import build_agent_graph
from agents.nodes import AgentNodes
from agents.state import AgentState, HistoryMessage
from app.config import get_settings
from models.conversation import Conversation
from models.message import Message, MessageRole
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.vector_service import RetrievedChunk

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================
# Resultado tipado
# ============================================================
@dataclass
class ChatResult:
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    chunks_used: list[RetrievedChunk]
    rejected: bool
    rejection_reason: Optional[str]


# ============================================================
# Función principal
# ============================================================
async def process_chat_message(
    db: AsyncSession,
    embedding_service: EmbeddingService,
    llm_service: LLMService,
    user_id: uuid.UUID,
    question: str,
    conversation_id: Optional[uuid.UUID],
) -> ChatResult:
    """
    Procesa una pregunta del usuario y devuelve la respuesta del agente.
    """
    # ----- 1. Cargar o crear la conversación -----
    if conversation_id is None:
        conversation = await _create_conversation(db, user_id, question)
        history: list[HistoryMessage] = []
    else:
        conversation = await _load_conversation(db, conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFound(f"Conversación {conversation_id} no encontrada.")
        history = await _load_history(db, conversation.id)

    # ----- 2. Construir el estado inicial -----
    initial_state: AgentState = {
        "question": question,
        "user_id": user_id,
        "conversation_id": conversation.id,
        "history": history,
    }

    # ----- 3. Construir y ejecutar el grafo -----
    nodes = AgentNodes(
        db=db,
        embedding_service=embedding_service,
        llm_service=llm_service,
    )
    graph = build_agent_graph(nodes)

    logger.info(
        "Ejecutando agente para user=%s conv=%s",
        user_id, conversation.id,
    )
    final_state = await graph.ainvoke(initial_state)

    # ----- 4. Construir el resultado -----
    rejected = not final_state.get("has_sufficient_context", False)
    chunks_used = final_state.get("retrieved_chunks", []) if not rejected else []

    return ChatResult(
        conversation_id=conversation.id,
        message_id=final_state["assistant_message_id"],
        answer=final_state["answer"],
        chunks_used=chunks_used,
        rejected=rejected,
        rejection_reason=final_state.get("rejection_reason") if rejected else None,
    )


# ============================================================
# Excepciones
# ============================================================
class ConversationNotFound(Exception):
    """La conversación solicitada no existe o no pertenece al usuario."""


# ============================================================
# Helpers
# ============================================================
async def _create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    first_question: str,
) -> Conversation:
    """Crea una nueva conversación con título auto-generado de la primera pregunta."""
    title = first_question.strip()[:60]
    conversation = Conversation(user_id=user_id, title=title)
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    logger.info("Conversación creada: id=%s title=%r", conversation.id, title)
    return conversation


async def _load_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[Conversation]:
    """Carga una conversación verificando pertenencia al usuario."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def _load_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> list[HistoryMessage]:
    """Carga los últimos N mensajes para incluir como contexto conversacional."""
    n = settings.history_max_messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(n)
    )
    messages = list(result.scalars().all())
    messages.reverse()   # más antiguo primero (para que el LLM lea cronológicamente)

    return [
        HistoryMessage(role=m.role.value, content=m.content)
        for m in messages
    ]


async def delete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Elimina la conversación si pertenece al usuario.
    Los mensajes asociados se borran por CASCADE.

    Returns:
        True si se eliminó; False si no existe.
    """
    conversation = await _load_conversation(db, conversation_id, user_id)
    if conversation is None:
        return False
    await db.delete(conversation)
    await db.commit()
    return True
