"""
Dependencias compartidas para FastAPI (DI).

Milestone 2: `get_db`
Milestone 3: `get_current_user`
Milestone 4: `get_embedding_service`
Milestone 5: `get_llm_service`
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from models.user import User
from services.auth_service import verify_token
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.user_service import get_or_create_user


# ============================================================
# DB session
# ============================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provee una `AsyncSession` por request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================
# Autenticación
# ============================================================
bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="JWT")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Devuelve el `User` autenticado (o lo crea al primer login)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el header Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = await verify_token(credentials.credentials)
    user = await get_or_create_user(db, claims)
    return user


# ============================================================
# Embedding service (singleton vía app.state)
# ============================================================
def get_embedding_service(request: Request) -> EmbeddingService:
    """Devuelve la instancia única del modelo de embeddings."""
    service: Optional[EmbeddingService] = getattr(
        request.app.state, "embedding_service", None
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de embeddings no está disponible.",
        )
    return service


# ============================================================
# LLM service (singleton vía app.state)
# ============================================================
def get_llm_service(request: Request) -> LLMService:
    """
    Devuelve la instancia única del cliente Ollama, creada en lifespan
    y guardada en `app.state.llm_service`.
    """
    service: Optional[LLMService] = getattr(
        request.app.state, "llm_service", None
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio LLM no está disponible.",
        )
    return service
