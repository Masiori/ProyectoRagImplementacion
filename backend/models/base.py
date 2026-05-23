"""
Mixins reutilizables para todos los modelos.

- `UUIDMixin`: añade columna `id` UUID v4 como PK.
- `TimestampMixin`: añade `created_at` y `updated_at` con timezone.

Los modelos heredan de Base + uno o ambos mixins según necesidad.
"""

import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """PK UUID v4 generada en Python (no en la BD) para portabilidad."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Timestamps `created_at` y `updated_at` con timezone."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CreatedAtMixin:
    """Solo `created_at` con timezone (para tablas append-only como messages, chunks)."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
