
"""
Dependencias compartidas para FastAPI (DI).
 
Milestone 2 (existente):
  - `get_db`: provee una `AsyncSession` por request.
 
Milestone 3 (nuevo):
  - `get_current_user`: extrae JWT, valida, obtiene/crea User.
"""
 
from typing import AsyncGenerator, Optional
 
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
 
from db.session import AsyncSessionLocal
from models.user import User
from services.auth_service import verify_token
from services.user_service import get_or_create_user
 
 
# ============================================================
# DB session
# ============================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia que provee una `AsyncSession` por request.
 
    - Commit explícito si no hubo excepción.
    - Rollback automático si la excepción burbujeó al endpoint.
    - Cierre garantizado al final del request.
    """
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
# `auto_error=False`: si falta el header, FastAPI no lanza 403 automático.
# Nosotros decidimos: lanzamos 401 (más correcto semánticamente).
bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="JWT")
 
 
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependencia que devuelve el `User` autenticado.
 
    Flujo:
      1. Extrae el bearer token del header Authorization.
      2. Valida el JWT (firma + claims) contra Cognito.
      3. Obtiene/crea el User en BD.
 
    Cualquier fallo → 401.
 
    Uso en un endpoint:
        @router.get("/protegido")
        async def protegido(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el header Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
 
    # Valida el JWT y devuelve los claims (lanza 401 si falla)
    claims = await verify_token(credentials.credentials)
 
    # Busca o crea el usuario en la BD
    user = await get_or_create_user(db, claims)
    return user
