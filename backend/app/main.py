"""
Entrypoint de la aplicación FastAPI.

Milestone 2: ahora hay conexión a Postgres y endpoints /health/db y
/health/pgvector. El engine se prueba al arrancar y se cierra al apagar.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from controllers import health_controller
from db.session import engine

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
# Lifespan: hooks de arranque y parada
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Al arrancar: prueba la conexión a la BD (warning si falla, no aborta).
    Al apagar: cierra el pool del engine para liberar conexiones.
    """
    logger.info("Iniciando %s en modo %s", settings.app_name, settings.app_env)

    # Smoke test de conexión a Postgres
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Conexión a PostgreSQL establecida correctamente")
    except Exception as exc:
        logger.warning(
            "No se pudo conectar a la BD al arrancar: %s. "
            "El backend levantará igual; los endpoints que requieran BD "
            "fallarán hasta que la conexión esté disponible.",
            exc,
        )

    yield

    logger.info("Apagando %s, cerrando pool de BD", settings.app_name)
    await engine.dispose()


# ------------------------------------------------------------
# Instancia de FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    description="Agente inteligente RAG sobre gastronomía colombiana.",
    version="0.2.0",
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