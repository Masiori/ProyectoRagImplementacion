"""
Dependencias compartidas para FastAPI (DI).

Milestone 2 (existente):
  - `get_db`: provee una `AsyncSession` por request.

Milestone 3 (existente):
  - `get_current_user`: extrae JWT, valida, obtiene/crea User.

Milestone 4 (nuevo):
  - `get_embedding_service`: devuelve la instancia singleton del modelo
    de embeddings cargada en el lifespan.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from models.user import User
from services.auth_service import verify_token
from services.embedding_service import EmbeddingService
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
    """
    Devuelve la instancia única del modelo de embeddings, cargada
    en `lifespan` y guardada en `app.state.embedding_service`.

    Si por algún motivo no está disponible, devolvemos 503.
    """
    service: Optional[EmbeddingService] = getattr(
        request.app.state, "embedding_service", None
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de embeddings no está disponible.",
        )
    return service