"""
Entrypoint de la aplicación FastAPI.

Milestone 5: cargamos el LLMService (cliente Ollama) en el lifespan y
registramos el router de chat.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from controllers import (
    auth_controller,
    chat_controller,
    documents_controller,
    health_controller,
)
from db.session import engine
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService

settings = get_settings()

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Al arrancar:
      - Smoke test de BD.
      - Carga del modelo de embeddings (~120 MB).
      - Inicialización del cliente Ollama.
    Al apagar:
      - Cierre del pool de BD.
    """
    logger.info("Iniciando %s en modo %s", settings.app_name, settings.app_env)

    # --- BD ---
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Conexión a PostgreSQL establecida correctamente")
    except Exception as exc:
        logger.warning(
            "No se pudo conectar a la BD al arrancar: %s. "
            "El backend levantará igual.",
            exc,
        )

    # --- Cognito ---
    if not settings.cognito_is_configured:
        logger.warning(
            "Cognito NO está configurado. Los endpoints protegidos "
            "devolverán 503 hasta que se configuren las variables COGNITO_*."
        )

    # --- S3 ---
    if not settings.s3_is_configured:
        logger.warning(
            "S3 NO está configurado. Las cargas y borrados de documentos "
            "fallarán hasta que se configuren las variables AWS_*."
        )

    # --- Modelo de embeddings ---
    try:
        logger.info("Cargando modelo de embeddings...")
        app.state.embedding_service = EmbeddingService()
    except Exception as exc:
        logger.exception("Error cargando el modelo de embeddings: %s", exc)
        app.state.embedding_service = None

    # --- Cliente LLM (Ollama) ---
    try:
        logger.info("Inicializando cliente Ollama...")
        app.state.llm_service = LLMService()
    except Exception as exc:
        logger.exception("Error inicializando el cliente Ollama: %s", exc)
        app.state.llm_service = None

    yield

    logger.info("Apagando %s, cerrando pool de BD", settings.app_name)
    await engine.dispose()


# ------------------------------------------------------------
# Instancia de FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    description="Agente inteligente RAG sobre gastronomía colombiana.",
    version="0.5.0",
    debug=settings.debug,
    lifespan=lifespan,
)


# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# Routers
# ------------------------------------------------------------
app.include_router(health_controller.router)
app.include_router(auth_controller.router)
app.include_router(documents_controller.router)
app.include_router(chat_controller.router)


# ------------------------------------------------------------
# Endpoints base
# ------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """Health check público (no toca BD)."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": app.version,
        "environment": settings.app_env,
    }


@app.get("/", tags=["system"])
async def root():
    """Endpoint raíz informativo."""
    return {
        "message": f"Bienvenido a {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }
