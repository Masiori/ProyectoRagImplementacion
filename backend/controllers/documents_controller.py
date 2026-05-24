"""
Controlador de documentos.

Endpoints:
  POST   /api/documents               → sube un archivo (multipart)
  GET    /api/documents               → lista los documentos del usuario
  GET    /api/documents/{id}          → detalle (incluye error_message)
  DELETE /api/documents/{id}          → borra documento + chunks + S3
  GET    /api/documents/{id}/chunks   → DEBUG: lista chunks paginados (sin filtro user)
  POST   /api/documents/{id}/reprocess → relanza el pipeline (útil si quedó en 'processing')

Todos los endpoints salvo `/chunks` requieren JWT y filtran por user_id.
"""

import logging
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_current_user, get_db, get_embedding_service
from models.chunk import Chunk
from models.document import Document, DocumentStatus
from models.user import User
from schemas.document import (
    ChunkListResponse,
    ChunkResponse,
    DocumentDetailResponse,
    DocumentResponse,
)
from services import s3_service
from services.document_service import (
    delete_document_completely,
    process_document_task,
)
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/documents", tags=["documents"])


# ============================================================
# POST /api/documents — Upload
# ============================================================
@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> Document:
    """
    Sube un archivo y dispara su procesamiento en background.

    - Valida mime_type contra `ALLOWED_MIME_TYPES`.
    - Valida tamaño contra `MAX_UPLOAD_SIZE_BYTES`.
    - Sube a S3.
    - Crea fila en `documents` con status='pending'.
    - Lanza BackgroundTask que cambia status a 'processing' → 'ready'.
    - Responde 202 inmediato con los datos del documento (status=pending).
    """
    # --- Validar MIME ---
    if file.content_type not in settings.allowed_mime_types_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"MIME type '{file.content_type}' no soportado. "
                f"Permitidos: {settings.allowed_mime_types_list}"
            ),
        )

    # --- Leer y validar tamaño ---
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío.",
        )
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"El archivo excede el tamaño máximo "
                f"({settings.max_upload_size_bytes} bytes)."
            ),
        )

    # --- Generar IDs y construir clave S3 ---
    document_id = uuid.uuid4()
    s3_key = s3_service.build_object_key(
        user_id=current_user.id,
        document_id=document_id,
        filename=file.filename or "unnamed",
    )

    # --- Subir a S3 ---
    try:
        await s3_service.upload_bytes(s3_key, contents, file.content_type)
    except s3_service.S3Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error subiendo a S3: {exc}",
        )

    # --- Crear fila en BD ---
    document = Document(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename or "unnamed",
        s3_key=s3_key,
        mime_type=file.content_type,
        size_bytes=len(contents),
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # --- Lanzar procesamiento en background ---
    # IMPORTANTE: pasamos embedding_service como referencia; la BG task
    # corre DESPUÉS de que cerremos esta sesión, así que la task abre la suya.
    background_tasks.add_task(
        process_document_task,
        document_id=document.id,
        embedding_service=embedding_service,
    )

    logger.info(
        "Upload aceptado: user=%s doc=%s filename=%s size=%d",
        current_user.id, document.id, document.filename, len(contents),
    )
    return document


# ============================================================
# GET /api/documents — Listar
# ============================================================
@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    """Lista todos los documentos del usuario autenticado."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


# ============================================================
# GET /api/documents/{id} — Detalle
# ============================================================
@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Detalle de un documento del usuario actual."""
    document = await _get_user_document_or_404(db, document_id, current_user.id)
    return document


# ============================================================
# DELETE /api/documents/{id}
# ============================================================
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Borra el documento, sus chunks (CASCADE) y el archivo en S3."""
    document = await _get_user_document_or_404(db, document_id, current_user.id)
    await delete_document_completely(db, document)


# ============================================================
# POST /api/documents/{id}/reprocess
# ============================================================
@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> Document:
    """
    Vuelve a lanzar el pipeline de procesamiento.

    Útil si un documento quedó atascado en 'processing' (p.ej. el
    contenedor reinició a mitad) o falló en 'failed' y queremos reintentar.

    Limpia los chunks existentes antes de reprocesar para evitar duplicados.
    """
    document = await _get_user_document_or_404(db, document_id, current_user.id)

    # Limpiar chunks existentes (si los hay)
    existing_chunks = await db.execute(
        select(Chunk).where(Chunk.document_id == document.id)
    )
    for chunk in existing_chunks.scalars():
        await db.delete(chunk)

    document.status = DocumentStatus.PENDING
    document.error_message = None
    await db.flush()
    await db.refresh(document)

    background_tasks.add_task(
        process_document_task,
        document_id=document.id,
        embedding_service=embedding_service,
    )
    return document


# ============================================================
# GET /api/documents/{id}/chunks — DEBUG
# ============================================================
# Endpoint de debug: NO filtra por user_id (acordado).
# Sigue requiriendo JWT como protección mínima.
# ============================================================
@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def list_chunks(
    document_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),  # solo auth, sin filtro
    db: AsyncSession = Depends(get_db),
) -> ChunkListResponse:
    """
    Lista los chunks de un documento (paginados).

    Endpoint de debug: cualquier usuario autenticado puede ver los chunks
    de cualquier documento. Útil para verificar el pipeline durante M4/M5.
    """
    # Conteo total
    count_result = await db.execute(
        select(func.count())
        .select_from(Chunk)
        .where(Chunk.document_id == document_id)
    )
    total = count_result.scalar_one()

    # Página
    result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
        .limit(limit)
        .offset(offset)
    )
    chunks = list(result.scalars().all())

    return ChunkListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[ChunkResponse.model_validate(c) for c in chunks],
    )


# ============================================================
# Helpers
# ============================================================
async def _get_user_document_or_404(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document:
    """Carga un documento verificando que pertenezca al usuario."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado.",
        )
    return document
