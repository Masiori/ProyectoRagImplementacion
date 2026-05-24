"""
Controlador de autenticación.

Endpoint:
  GET /me  → devuelve los datos del usuario autenticado.
             Sirve también como "ping de sesión" desde el frontend.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from models.user import User
from schemas.user import UserResponse

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Devuelve el perfil del usuario autenticado.

    - Si el token es válido y el usuario existe → 200 con sus datos.
    - Si el token es válido pero el usuario no existe → se crea
      automáticamente (al primer login) y se devuelve.
    - Cualquier problema con el token → 401.
    """
    return current_user
