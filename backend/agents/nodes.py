"""
Nodos del agente LangGraph.

Los 6 nodos viven como métodos de la clase `AgentNodes`. Construimos
una instancia por request (en `chat_service`) inyectando las dependencias
que cada nodo necesita.

Nodos:
  1. receive_question     → normaliza
  2. retrieve_context     → embedding query + búsqueda pgvector
  3. evaluate_relevance   → compara contra umbral
  4. generate_answer      → llama al LLM
  5. reject_question      → devuelve frase canónica
  6. save_history         → INSERT user + assistant messages

Aristas condicionales:
  - route_after_evaluate decide entre generate_answer y reject_question
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from agents.prompts import CANONICAL_REJECTION, SYSTEM_PROMPT, build_user_prompt
from agents.state import AgentState
from app.config import get_settings
from models.message import Message, MessageRole
from services.embedding_service import EmbeddingService
from services.llm_service import LLMError, LLMService
from services.vector_service import RetrievedChunk, search_chunks

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentNodes:
    """Contiene los 6 nodos del agente, inyectando las dependencias."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.llm_service = llm_service

    # ============================================================
    # NODO 1 — receive_question
    # ============================================================
    async def receive_question(self, state: AgentState) -> dict:
        """Normaliza la pregunta. Validación de longitud ya se hizo en el controller."""
        question = state["question"].strip()
        logger.info(
            "[Nodo receive_question] user=%s conv=%s question='%s...'",
            state["user_id"],
            state["conversation_id"],
            question[:60],
        )
        return {"question": question}

    # ============================================================
    # NODO 2 — retrieve_context
    # ============================================================
    async def retrieve_context(self, state: AgentState) -> dict:
        """Genera embedding de la pregunta y busca top-K chunks en pgvector."""
        question = state["question"]
        user_id = state["user_id"]

        # Embedding de la pregunta (con prefijo 'query: ' aplicado por el servicio)
        query_embedding = await self.embedding_service.embed_query(question)

        # Búsqueda vectorial filtrada por el usuario
        chunks = await search_chunks(
            db=self.db,
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=settings.top_k,
        )

        best_sim = chunks[0].similarity if chunks else 0.0
        logger.info(
            "[Nodo retrieve_context] chunks=%d best_similarity=%.3f",
            len(chunks), best_sim,
        )
        return {
            "retrieved_chunks": chunks,
            "best_similarity": best_sim,
        }

    # ============================================================
    # NODO 3 — evaluate_relevance
    # ============================================================
    async def evaluate_relevance(self, state: AgentState) -> dict:
        """
        Compara la mejor similitud contra `SIMILARITY_THRESHOLD`.
        Decide si el agente tiene contexto suficiente para responder.
        """
        best_sim = state.get("best_similarity", 0.0)
        chunks = state.get("retrieved_chunks", [])
        threshold = settings.similarity_threshold

        if not chunks:
            has_context = False
            reason = "no_chunks"
        elif best_sim < threshold:
            has_context = False
            reason = "low_similarity"
        else:
            has_context = True
            reason = None

        logger.info(
            "[Nodo evaluate_relevance] best=%.3f threshold=%.3f decision=%s reason=%s",
            best_sim, threshold,
            "ANSWER" if has_context else "REJECT", reason,
        )
        return {
            "has_sufficient_context": has_context,
            "rejection_reason": reason,
        }

    # ============================================================
    # NODO 4 — generate_answer
    # ============================================================
    async def generate_answer(self, state: AgentState) -> dict:
        """Construye el prompt con contexto + historial y llama al LLM."""
        question = state["question"]
        chunks: list[RetrievedChunk] = state.get("retrieved_chunks", [])
        history = state.get("history", [])

        user_prompt = build_user_prompt(question, chunks, history)

        try:
            answer = await self.llm_service.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
        except LLMError as exc:
            logger.error("[Nodo generate_answer] LLM falló: %s", exc)
            # Si el LLM falla, devolvemos la respuesta canónica como fallback
            # (mejor que dejar la conversación rota)
            return {
                "answer": CANONICAL_REJECTION,
                "rejection_reason": "llm_error",
                "has_sufficient_context": False,
            }

        logger.info(
            "[Nodo generate_answer] respuesta generada (%d chars)",
            len(answer),
        )
        return {"answer": answer}

    # ============================================================
    # NODO 5 — reject_question
    # ============================================================
    async def reject_question(self, state: AgentState) -> dict:
        """Devuelve la respuesta canónica cuando no hay contexto suficiente."""
        reason = state.get("rejection_reason", "low_similarity")
        logger.info("[Nodo reject_question] motivo=%s", reason)
        return {"answer": CANONICAL_REJECTION}

    # ============================================================
    # NODO 6 — save_history
    # ============================================================
    async def save_history(self, state: AgentState) -> dict:
        """
        Persiste el intercambio en la BD: 2 filas en `messages`.

        - Una con role='user', content=pregunta
        - Una con role='assistant', content=respuesta, sources=[{...}]
          (sources solo si hubo respuesta basada en contexto)
        """
        conversation_id = state["conversation_id"]
        question = state["question"]
        answer = state["answer"]
        chunks = state.get("retrieved_chunks", [])
        has_context = state.get("has_sufficient_context", False)

        # Mensaje del usuario
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=question,
            sources=None,
        )
        self.db.add(user_msg)

        # Sources solo si hubo respuesta basada en contexto
        sources_payload = None
        if has_context and chunks:
            sources_payload = [
                {
                    "chunk_id": str(c.chunk_id),
                    "document_id": str(c.document_id),
                    "filename": c.filename,
                    "similarity": round(c.similarity, 4),
                }
                for c in chunks
            ]

        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=answer,
            sources=sources_payload,
        )
        self.db.add(assistant_msg)

        await self.db.flush()
        await self.db.refresh(assistant_msg)

        logger.info(
            "[Nodo save_history] persistidos user + assistant (msg_id=%s)",
            assistant_msg.id,
        )
        return {"assistant_message_id": assistant_msg.id}

    # ============================================================
    # ROUTER — arista condicional después de evaluate_relevance
    # ============================================================
    def route_after_evaluate(self, state: AgentState) -> str:
        """Decide a qué nodo ir tras la evaluación de relevancia."""
        return "generate_answer" if state.get("has_sufficient_context") else "reject_question"
