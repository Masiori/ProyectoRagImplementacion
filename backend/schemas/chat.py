"""
Schemas Pydantic para los endpoints de chat.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings

settings = get_settings()


# ============================================================
# Request
# ============================================================
class ChatRequest(BaseModel):
    """Cuerpo del POST /api/chat."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_question_length,
        description="Pregunta del usuario.",
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Si se omite, se crea una conversación nueva.",
    )


# ============================================================
# Source (chunk usado para responder)
# ============================================================
class Source(BaseModel):
    """Fuente que el agente usó para responder."""

    chunk_id: UUID
    document_id: UUID
    filename: str
    similarity: float


# ============================================================
# Response
# ============================================================
class ChatResponse(BaseModel):
    """Respuesta del POST /api/chat."""

    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: list[Source]
    rejected: bool
    rejection_reason: Optional[str] = None


# ============================================================
# Conversaciones
# ============================================================
class ConversationResponse(BaseModel):
    """Forma básica de una conversación (para listados)."""

    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Mensaje individual dentro de una conversación."""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    sources: Optional[list[dict]] = None    # JSONB tal cual está en la BD
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    """Conversación con todos sus mensajes."""

    messages: list[MessageResponse]
