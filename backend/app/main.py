"""
Entrypoint de la aplicación FastAPI.

Milestone 1: solo expone un endpoint /health para validar que la app
arranca correctamente. La lógica de negocio se irá agregando en los
siguientes milestones.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

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
# Aquí, en milestones futuros, conectaremos:
#   - Pool de PostgreSQL (Milestone 2)
#   - Modelo de embeddings (Milestone 4)
#   - Cliente Ollama (Milestone 5)
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hook de inicio/parada de la aplicación."""
    logger.info("Iniciando %s en modo %s", settings.app_name, settings.app_env)
    yield
    logger.info("Apagando %s", settings.app_name)


# ------------------------------------------------------------
# Instancia de FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    description="Agente inteligente RAG sobre gastronomía colombiana.",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# ------------------------------------------------------------
# CORS
# Se prepara aquí; en Milestone 6 se ajustará a la URL real del frontend.
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# Endpoints base
# ------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check público. Útil para:
    - Validar que la app responde
    - Health checks de Docker / load balancer
    - Pruebas de despliegue
    """
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
