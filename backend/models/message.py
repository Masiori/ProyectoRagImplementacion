"""
Modelo `Message`.

Un mensaje individual dentro de una conversación. Solo guardamos
mensajes de roles `user` y `assistant`; el `system` prompt vive en
código y no se persiste.

La columna `sources` (JSONB) almacena los chunks utilizados por el
agente para fundamentar su respuesta. Solo se rellena en mensajes
con role='assistant'.
"""

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.base import CreatedAtMixin, UUIDMixin

if TYPE_CHECKING:
    from models.conversation import Conversation


class MessageRole(str, PyEnum):
    """Rol del autor del mensaje."""

    USER = "user"            # Lo que escribe el humano
    ASSISTANT = "assistant"  # Lo que responde el agente


class Message(Base, UUIDMixin, CreatedAtMixin):
    """Mensaje individual en una conversación."""

    __tablename__ = "messages"

    # ------------------------------------------------------------
    # FK a la conversación
    # CASCADE: borrar la conversación borra sus mensajes.
    # ------------------------------------------------------------
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------
    # Rol
    # ------------------------------------------------------------
    # `values_callable` fuerza a usar los .value ('user', 'assistant')
    # como valores del enum en PostgreSQL en vez de los nombres de los
    # miembros ('USER', 'ASSISTANT').
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(
            MessageRole,
            name="message_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ------------------------------------------------------------
    # Fuentes (solo para mensajes del assistant)
    # ------------------------------------------------------------
    # Estructura esperada (lista de objetos):
    # [{"chunk_id": "...", "document_id": "...", "filename": "...",
    #   "similarity": 0.83, "snippet": "..."}, ...]
    sources: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------
    # Relación
    # ------------------------------------------------------------
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role.value}>"