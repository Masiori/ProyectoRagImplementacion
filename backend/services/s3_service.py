"""
Servicio S3.

Provee una capa async sobre boto3 (que es síncrono). Las operaciones
bloqueantes se ejecutan en un thread pool con `asyncio.to_thread` para
no congelar el event loop de FastAPI.

Path convention:
    users/{user_id}/documents/{document_id}/{filename}
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class S3Error(Exception):
    """Error genérico de operaciones S3."""


# ============================================================
# Cliente boto3 (lazy)
# ============================================================
_s3_client = None


def _get_client():
    """Construye (o reutiliza) el cliente boto3."""
    global _s3_client
    if _s3_client is None:
        if not settings.s3_is_configured:
            raise S3Error(
                "S3 no está configurado: define AWS_S3_BUCKET, "
                "AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY en .env."
            )
        _s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _s3_client


# ============================================================
# Helpers de path
# ============================================================
def build_object_key(user_id: UUID, document_id: UUID, filename: str) -> str:
    """Construye la clave S3 para un documento."""
    return f"users/{user_id}/documents/{document_id}/{filename}"


# ============================================================
# Operaciones
# ============================================================
async def upload_bytes(
    key: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> None:
    """Sube bytes a S3 bajo la clave dada."""
    def _sync_upload():
        client = _get_client()
        extra = {"ContentType": content_type} if content_type else {}
        try:
            client.put_object(
                Bucket=settings.aws_s3_bucket,
                Key=key,
                Body=data,
                **extra,
            )
        except (BotoCoreError, ClientError) as exc:
            raise S3Error(f"Error subiendo a S3: {exc}") from exc

    await asyncio.to_thread(_sync_upload)
    logger.info("S3 upload OK: s3://%s/%s (%d bytes)",
                settings.aws_s3_bucket, key, len(data))


async def download_bytes(key: str) -> bytes:
    """Descarga el objeto S3 y devuelve sus bytes."""
    def _sync_download() -> bytes:
        client = _get_client()
        try:
            response = client.get_object(Bucket=settings.aws_s3_bucket, Key=key)
            return response["Body"].read()
        except (BotoCoreError, ClientError) as exc:
            raise S3Error(f"Error descargando de S3: {exc}") from exc

    data = await asyncio.to_thread(_sync_download)
    logger.info("S3 download OK: s3://%s/%s (%d bytes)",
                settings.aws_s3_bucket, key, len(data))
    return data


async def delete_object(key: str) -> None:
    """Elimina un objeto de S3. No falla si no existe."""
    def _sync_delete():
        client = _get_client()
        try:
            client.delete_object(Bucket=settings.aws_s3_bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise S3Error(f"Error eliminando de S3: {exc}") from exc

    await asyncio.to_thread(_sync_delete)
    logger.info("S3 delete OK: s3://%s/%s", settings.aws_s3_bucket, key)
