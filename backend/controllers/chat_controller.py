"""
Controlador de chat.

Endpoints:
  POST   /api/chat                              → enviar pregunta
  GET    /api/chat/conversations                → listar conversaciones del usuario
  GET    /api/chat/conversations/{id}           → detalle + mensajes
  DELETE /api/chat/conversations/{id}           → borrar conversación + mensajes (CASCADE)

Todos requieren JWT y filtran por user_id.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_current_user,
    get_db,
    get_embedding_service,
    get_llm_service,
)
from models.conversation import Conversation
from models.message import Message
from models.user import User
from schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
    Source,
)
from services import chat_service
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ============================================================
# POST /api/chat
# ============================================================
@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    llm_service: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    """
    Procesa una pregunta del usuario.

    - Si `conversation_id` se provee, continúa una conversación existente.
    - Si no, se crea una nueva con título auto-generado.
    - El agente decide si responder o rechazar según el contexto.
    """
    try:
        result = await chat_service.process_chat_message(
            db=db,
            embedding_service=embedding_service,
            llm_service=llm_service,
            user_id=current_user.id,
            question=request.question,
            conversation_id=request.conversation_id,
        )
    except chat_service.ConversationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada.",
        )

    sources = [
        Source(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            similarity=round(c.similarity, 4),
        )
        for c in result.chunks_used
    ]

    return ChatResponse(
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        answer=result.answer,
        sources=sources,
        rejected=result.rejected,
        rejection_reason=result.rejection_reason,
    )


# ============================================================
# GET /api/chat/conversations
# ============================================================
@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    """Lista todas las conversaciones del usuario, más recientes primero."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


# ============================================================
# GET /api/chat/conversations/{id}
# ============================================================
@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    """Devuelve la conversación con todos sus mensajes ordenados cronológicamente."""
    # Verificar pertenencia
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada.",
        )

    # Cargar mensajes
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = list(msg_result.scalars().all())

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


# ============================================================
# DELETE /api/chat/conversations/{id}
# ============================================================
@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Borra la conversación y todos sus mensajes (CASCADE)."""
    deleted = await chat_service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada.",
        )
