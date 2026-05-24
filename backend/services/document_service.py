"""
Orquestador de procesamiento de documentos.

Función principal: `process_document_task` — diseñada para correr como
BackgroundTask de FastAPI.

Pipeline:
    pending → processing → (S3 download → extract → chunk → embed → insert) → ready
                       \\__ si falla en cualquier paso __ → failed + error_message
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from models.chunk import Chunk
from models.document import Document, DocumentStatus
from services import s3_service
from services.chunking_service import chunk_text
from services.embedding_service import EmbeddingService
from services.extraction_service import extract_text

logger = logging.getLogger(__name__)


async def process_document_task(
    document_id: uuid.UUID,
    embedding_service: EmbeddingService,
) -> None:
    """
    BackgroundTask que procesa un documento de pending → ready.

    Crea su propia sesión de BD porque la sesión del request original
    ya estará cerrada cuando esta función corra.
    """
    logger.info("Iniciando procesamiento de documento %s", document_id)

    async with AsyncSessionLocal() as db:
        # 1. Cargar el documento
        document = await _load_document(db, document_id)
        if document is None:
            logger.error("Documento %s no encontrado al procesar", document_id)
            return

        try:
            # 2. Marcar como 'processing'
            document.status = DocumentStatus.PROCESSING
            document.error_message = None
            await db.commit()

            # 3. Descargar de S3
            logger.info("Descargando de S3: %s", document.s3_key)
            file_bytes = await s3_service.download_bytes(document.s3_key)

            # 4. Extraer texto
            text = await extract_text(file_bytes, document.mime_type)

            # 5. Chunking
            chunks_texts = await chunk_text(text)
            if not chunks_texts:
                raise RuntimeError("El chunking no produjo fragmentos.")

            # 6. Embeddings
            logger.info("Generando embeddings para %d chunks", len(chunks_texts))
            vectors = await embedding_service.embed_passages(chunks_texts)

            # 7. Insertar chunks en BD
            await _insert_chunks(db, document.id, chunks_texts, vectors)

            # 8. Marcar como 'ready'
            document.status = DocumentStatus.READY
            await db.commit()

            logger.info(
                "Documento %s procesado correctamente (%d chunks)",
                document_id, len(chunks_texts),
            )

        except Exception as exc:
            logger.exception("Error procesando documento %s", document_id)
            # Recargar la fila (puede estar stale después de un rollback)
            await db.rollback()
            doc = await _load_document(db, document_id)
            if doc is not None:
                doc.status = DocumentStatus.FAILED
                doc.error_message = str(exc)[:1000]  # cap para no romper TEXT
                await db.commit()


# ============================================================
# Helpers
# ============================================================
async def _load_document(
    db: AsyncSession,
    document_id: uuid.UUID,
) -> Document | None:
    """Carga un documento por id."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    return result.scalar_one_or_none()


async def _insert_chunks(
    db: AsyncSession,
    document_id: uuid.UUID,
    contents: list[str],
    vectors: list[list[float]],
) -> None:
    """Inserta los chunks de un documento en una sola transacción."""
    chunks = [
        Chunk(
            document_id=document_id,
            chunk_index=idx,
            content=content,
            embedding=vector,
        )
        for idx, (content, vector) in enumerate(zip(contents, vectors))
    ]
    db.add_all(chunks)
    await db.flush()


async def delete_document_completely(
    db: AsyncSession,
    document: Document,
) -> None:
    """
    Borra un documento de BD y su archivo en S3.

    Los chunks asociados se borran automáticamente por CASCADE.
    Si la eliminación en S3 falla, igual borramos la fila (la consistencia
    se prioriza al nivel BD).
    """
    s3_key = document.s3_key

    # Borrar de BD primero (CASCADE limpia chunks)
    await db.delete(document)
    await db.commit()

    # Borrar de S3 (best-effort)
    try:
        await s3_service.delete_object(s3_key)
    except s3_service.S3Error as exc:
        logger.warning(
            "BD eliminó el doc pero S3 falló: %s. Key huérfana: %s",
            exc, s3_key,
        )
