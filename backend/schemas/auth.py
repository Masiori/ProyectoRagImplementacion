"""
Schemas Pydantic para autenticación.

`TokenClaims` representa los claims que esperamos en el ID token de Cognito.
Se usa internamente para tipar el flujo de validación; no se devuelve al cliente.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TokenClaims(BaseModel):
    """
    Claims relevantes del ID token de Cognito.

    No incluye todos los claims posibles; solo los que el backend usa.
    Permite campos extra (model_config) para no romper si Cognito agrega
    nuevos claims en el futuro.
    """

    sub: str                            # Identidad única del usuario
    email: str
    token_use: str                      # Debe ser "id"
    iss: str                            # Issuer
    aud: str                            # Audience (App Client ID)
    exp: int                            # Expiration timestamp
    iat: int                            # Issued at timestamp

    # `identities` solo aparece cuando el usuario entró por un IdP federado
    # (Google, etc.). Si entró con email/password directo de Cognito, no existe.
    identities: Optional[list[dict[str, Any]]] = None

    model_config = ConfigDict(extra="allow")
