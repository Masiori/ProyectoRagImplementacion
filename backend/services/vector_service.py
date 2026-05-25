"""
Servicio de búsqueda vectorial.

Busca chunks relevantes en pgvector, filtrando por usuario.
Usa el operador de distancia coseno (`<=>`) que pgvector expone como
`Vector.cosine_distance()` en SQLAlchemy.

similitud = 1 - distancia_coseno  (mayor = más similar; rango [0, 1] aprox)
"""

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from models.chunk import Chunk
from models.document import Document

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RetrievedChunk:
    """Resultado de la búsqueda vectorial."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    filename: str
    similarity: float


async def search_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    user_id: uuid.UUID,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Busca los top-K chunks más similares al embedding de la pregunta,
    restringidos a documentos del usuario indicado.

    Returns:
        Lista ordenada por similitud descendente. Vacía si no hay
        documentos del usuario con embeddings.
    """
    top_k = top_k if top_k is not None else settings.top_k

    # `Chunk.embedding.cosine_distance(...)` se traduce al operador `<=>`
    # de pgvector. Distancia coseno: 0 = idéntico, 2 = opuesto.
    distance = Chunk.embedding.cosine_distance(query_embedding)

    stmt = (
        select(
            Chunk.id.label("chunk_id"),
            Chunk.document_id.label("document_id"),
            Chunk.content.label("content"),
            Document.filename.label("filename"),
            distance.label("distance"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.user_id == user_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(top_k)
    )

    result = await db.execute(stmt)
    rows = result.all()

    chunks = [
        RetrievedChunk(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            content=row.content,
            filename=row.filename,
            similarity=max(0.0, 1.0 - float(row.distance)),
        )
        for row in rows
    ]

    if chunks:
        logger.info(
            "Retrieval: %d chunks recuperados, mejor similitud=%.3f",
            len(chunks), chunks[0].similarity,
        )
    else:
        logger.info(
            "Retrieval: 0 chunks recuperados (¿usuario sin documentos?)"
        )

    return chunks
