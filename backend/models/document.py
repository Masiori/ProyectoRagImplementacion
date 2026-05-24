"""
Modelo `Document`.

Representa un archivo subido por un usuario. Pasa por estados:
pending → processing → ready (o failed). Su contenido se almacena en
S3 (`s3_key`) y sus chunks vectorizados viven en la tabla `chunks`.
"""

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.chunk import Chunk
    from models.user import User


class DocumentStatus(str, PyEnum):
    """Ciclo de vida de un documento."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    """Documento subido por un usuario."""

    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_key: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        unique=True,
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(
            DocumentStatus,
            name="document_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=DocumentStatus.PENDING,
        server_default=DocumentStatus.PENDING.value,
        index=True,
    )

    # ------------------------------------------------------------
    # Mensaje de error (solo cuando status='failed')
    # ------------------------------------------------------------
    # Texto descriptivo del fallo durante el procesamiento.
    # NULL en cualquier otro estado.
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="documents")

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status.value}>"