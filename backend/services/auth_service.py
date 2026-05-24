"""
Servicio de autenticación: validación de JWTs de AWS Cognito.

Flujo de `verify_token`:
  1. Decodifica el header (sin firma) → obtiene `kid`
  2. Obtiene JWKS de Cognito (cacheadas)
  3. Busca la clave pública por `kid`
  4. Verifica firma + claims (aud, iss, exp) con python-jose
  5. Valida manualmente `token_use == 'id'`
  6. Devuelve los claims tipados como `TokenClaims`

El cache de JWKS dura 1 hora. Se usa un asyncio.Lock para evitar que
múltiples requests simultáneas hagan la descarga al mismo tiempo cuando
expira.
"""

import asyncio
import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import (
    ExpiredSignatureError,
    JWKError,
    JWTClaimsError,
    JWTError,
)

from app.config import get_settings
from schemas.auth import TokenClaims

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================
# Constantes
# ============================================================
JWKS_CACHE_TTL_SECONDS = 3600   # Re-descarga JWKS cada hora
JWT_LEEWAY_SECONDS = 0          # Sin tolerancia: token vencido = rechazado
ALGORITHMS = ["RS256"]          # Cognito firma con RS256


# ============================================================
# Cache de JWKS
# ============================================================
_jwks_cache: dict[str, Any] = {"data": None, "expires_at": 0.0}
_jwks_lock = asyncio.Lock()


async def _fetch_jwks() -> dict:
    """Descarga JWKS desde Cognito. Llamado solo cuando el cache expira."""
    url = settings.cognito_jwks_url
    logger.info("Descargando JWKS desde %s", url)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def get_jwks() -> dict:
    """
    Devuelve las JWKS de Cognito. Usa cache de `JWKS_CACHE_TTL_SECONDS`.
    Thread-safe entre tareas asyncio gracias al lock.
    """
    async with _jwks_lock:
        now = time.time()
        if _jwks_cache["data"] is not None and now < _jwks_cache["expires_at"]:
            return _jwks_cache["data"]

        try:
            jwks = await _fetch_jwks()
        except httpx.HTTPError as exc:
            logger.error("Error descargando JWKS: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo obtener las claves públicas de Cognito.",
            )

        _jwks_cache["data"] = jwks
        _jwks_cache["expires_at"] = now + JWKS_CACHE_TTL_SECONDS
        return jwks


def _find_key_by_kid(jwks: dict, kid: str) -> dict | None:
    """Busca la clave pública en el set de JWKS por su `kid`."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


# ============================================================
# Validación de tokens
# ============================================================
async def verify_token(token: str) -> TokenClaims:
    """
    Valida un JWT de Cognito y devuelve sus claims tipados.

    Levanta `HTTPException(401)` en cualquier fallo de validación,
    con un detalle genérico para no filtrar información a atacantes.
    """
    if not settings.cognito_is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Cognito no está configurado. Define "
                "COGNITO_USER_POOL_ID y COGNITO_APP_CLIENT_ID en .env."
            ),
        )

    # --- Paso 1: leer el header sin verificar ---
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        logger.debug("Header malformado: %s", exc)
        raise _unauthorized("Token malformado.")

    kid = unverified_header.get("kid")
    if not kid:
        raise _unauthorized("Token sin 'kid' en el header.")

    # --- Paso 2 y 3: obtener JWKS y buscar clave por kid ---
    jwks = await get_jwks()
    public_key = _find_key_by_kid(jwks, kid)

    if public_key is None:
        # Posiblemente Cognito rotó las claves y nuestro cache está obsoleto.
        # Invalidamos el cache y reintentamos UNA vez.
        logger.warning("kid %s no encontrado en cache, refrescando JWKS", kid)
        _jwks_cache["expires_at"] = 0
        jwks = await get_jwks()
        public_key = _find_key_by_kid(jwks, kid)
        if public_key is None:
            raise _unauthorized("Clave pública del token no encontrada.")

    # --- Paso 4: verificar firma + claims estándar ---
    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            audience=settings.cognito_app_client_id,
            issuer=settings.cognito_issuer,
            options={
                # Cognito no incluye `at_hash` en ID tokens cuando no hay nonce,
                # así que desactivamos esa verificación opcional.
                "verify_at_hash": False,
            },
            # `leeway` se aplica a exp/iat/nbf
            # (python-jose >= 3.3 acepta el kwarg directamente)
        )
    except ExpiredSignatureError:
        raise _unauthorized("Token expirado.")
    except JWTClaimsError as exc:
        # Falló aud o iss
        logger.debug("Claims inválidos: %s", exc)
        raise _unauthorized("Claims inválidos en el token.")
    except (JWTError, JWKError) as exc:
        logger.debug("Firma o estructura inválida: %s", exc)
        raise _unauthorized("Token inválido.")

    # --- Paso 5: verificar token_use manualmente ---
    if claims.get("token_use") != "id":
        raise _unauthorized("Se esperaba un ID token.")

    # --- Paso 6: parsear a TokenClaims ---
    try:
        return TokenClaims(**claims)
    except Exception as exc:
        logger.warning("Claims del JWT no cumplen el schema esperado: %s", exc)
        raise _unauthorized("Estructura del token inesperada.")


def _unauthorized(detail: str) -> HTTPException:
    """Helper para construir respuestas 401 con WWW-Authenticate."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# ============================================================
# Helpers de extracción
# ============================================================
def extract_auth_provider(claims: TokenClaims) -> str:
    """
    Determina el proveedor de autenticación a partir de los claims.
      - Si `identities` está presente y el primer elemento tiene
        providerName='Google' → 'google'
      - Si no hay `identities` → 'cognito' (login email/password directo)
    """
    if claims.identities:
        provider = (claims.identities[0].get("providerName") or "").lower()
        if provider == "google":
            return "google"
    return "cognito"
