"""
Servicio de gestión de usuarios.

`get_or_create_user`:
  - Busca al usuario por `cognito_sub`.
  - Si existe, devuelve la fila (opcionalmente actualiza `email`).
  - Si no existe, lo crea con los datos del JWT.

Es el punto donde el usuario "aparece" en nuestra BD por primera vez,
sin necesidad de un flujo de registro explícito.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.auth import TokenClaims
from services.auth_service import extract_auth_provider

logger = logging.getLogger(__name__)


async def get_or_create_user(db: AsyncSession, claims: TokenClaims) -> User:
    """
    Devuelve el `User` correspondiente a los claims del JWT.

    Si el usuario no existe, lo crea con `cognito_sub`, `email` y
    `auth_provider` derivados del token.

    Si el usuario existe y su email cambió en Cognito, lo actualizamos
    localmente para mantener consistencia.
    """
    # Buscar por cognito_sub (la identidad estable)
    stmt = select(User).where(User.cognito_sub == claims.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        # Usuario ya existe; actualizar email si cambió
        if user.email != claims.email:
            logger.info(
                "Actualizando email de usuario %s: %s → %s",
                user.id, user.email, claims.email,
            )
            user.email = claims.email
            await db.flush()
        return user

    # Crear usuario nuevo
    auth_provider = extract_auth_provider(claims)
    user = User(
        cognito_sub=claims.sub,
        email=claims.email,
        auth_provider=auth_provider,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info(
        "Usuario creado: id=%s email=%s provider=%s",
        user.id, user.email, user.auth_provider,
    )
    return user
