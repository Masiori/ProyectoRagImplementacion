"""
Modelo `Chunk`.

Cada documento se divide en chunks (~800 caracteres). Cada chunk tiene
un embedding vectorial (Vector(384)) generado por el modelo
`multilingual-e5-small`. La búsqueda RAG opera sobre estos embeddings.

El embedding queda NULL hasta Milestone 4 (cuando se conecte el pipeline
de procesamiento). Pero la columna ya existe desde Milestone 2.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from db.base import Base
from models.base import CreatedAtMixin, UUIDMixin

if TYPE_CHECKING:
    from models.document import Document

settings = get_settings()


class Chunk(Base, UUIDMixin, CreatedAtMixin):
    """Fragmento de un documento, con su embedding vectorial."""

    __tablename__ = "chunks"

    # ------------------------------------------------------------
    # FK al documento padre
    # CASCADE: borrar el documento borra sus chunks automáticamente.
    # ------------------------------------------------------------
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Posición del chunk dentro del documento (0-indexed)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Texto del chunk
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ------------------------------------------------------------
    # Embedding vectorial
    # ------------------------------------------------------------
    # Nullable porque al crear el chunk aún no se ha calculado.
    # Se rellena durante el procesamiento async del documento.
    # Dimensión 384 = multilingual-e5-small.
    # ------------------------------------------------------------
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(settings.embedding_dimension),
        nullable=True,
    )

    # ------------------------------------------------------------
    # Metadatos arbitrarios
    # ------------------------------------------------------------
    # Renombrado en Python a `chunk_metadata` porque `metadata` es
    # un atributo reservado de SQLAlchemy. La columna en SQL se llama
    # `metadata`.
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ------------------------------------------------------------
    # Relación
    # ------------------------------------------------------------
    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk id={self.id} doc={self.document_id} idx={self.chunk_index}>"
