"""
Controlador de health checks de infraestructura.

Endpoints:
  GET /health/db        → confirma conexión a Postgres
  GET /health/pgvector  → confirma que la extensión vector está instalada
  GET /health/ollama    → confirma que Ollama responde y el modelo está cargado
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_llm_service
from services.llm_service import LLMError, LLMService

router = APIRouter(prefix="/health", tags=["system"])


@router.get("/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    """Verifica que el backend puede ejecutar consultas contra Postgres."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "disconnected",
                "error": str(exc),
            },
        )


@router.get("/pgvector")
async def health_pgvector(db: AsyncSession = Depends(get_db)) -> dict:
    """Verifica que la extensión pgvector está instalada y reporta su versión."""
    try:
        result = await db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        version = result.scalar()
        if version is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "error", "pgvector": "not_installed"},
            )
        return {"status": "ok", "pgvector_version": version}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "pgvector": "unknown",
                "error": str(exc),
            },
        )


@router.get("/ollama")
async def health_ollama(
    llm_service: LLMService = Depends(get_llm_service),
) -> dict:
    """
    Verifica que Ollama responde y que el modelo configurado está cargado.

    Devuelve:
        - 200 + info del servicio si todo OK
        - 503 si Ollama no responde
        - 200 con `model_loaded=false` si responde pero el modelo no está
          (sin lanzar excepción: facilita el diagnóstico)
    """
    try:
        info = await llm_service.health_check()
        return {"status": "ok", **info}
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "error": str(exc)},
        )
