"""
Schemas Pydantic para documentos y chunks.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Document
# ============================================================
class DocumentResponse(BaseModel):
    """Forma básica de un documento (para listados)."""

    id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    """Forma detallada (incluye error_message si aplica)."""

    error_message: Optional[str] = None


# ============================================================
# Chunk
# ============================================================
class ChunkResponse(BaseModel):
    """Chunk individual (para debug en /documents/{id}/chunks)."""

    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    # `metadata` está renombrado en el modelo a `chunk_metadata` por colisión
    # con SQLAlchemy; aquí lo exponemos como `metadata` en la API.
    metadata: dict = Field(default_factory=dict, alias="chunk_metadata")
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ChunkListResponse(BaseModel):
    """Respuesta paginada de chunks."""

    total: int
    limit: int
    offset: int
    items: list[ChunkResponse]
