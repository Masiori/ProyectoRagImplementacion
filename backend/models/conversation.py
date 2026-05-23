"""
Modelo `Conversation`.

Agrupa los mensajes intercambiados entre un usuario y el agente en una
sesión de chat. El frontend puede mostrar varias conversaciones por
usuario; al borrar una, sus mensajes se borran en cascada.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.message import Message
    from models.user import User


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Hilo de mensajes entre un usuario y el agente."""

    __tablename__ = "conversations"

    # ------------------------------------------------------------
    # FK al usuario
    # RESTRICT: no se permite borrar usuarios con conversaciones activas.
    # ------------------------------------------------------------
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------
    # Título opcional (lo puede setear el usuario o auto-generarse con
    # la primera pregunta).
    # ------------------------------------------------------------
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="conversations")

    # Conversation → Message: CASCADE.
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user={self.user_id}>"
