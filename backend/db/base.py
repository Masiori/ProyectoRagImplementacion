"""
Base declarativa de SQLAlchemy.

Todos los modelos heredan de `Base`. Alembic usa `Base.metadata`
para detectar el esquema esperado y generar migraciones.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM del proyecto."""

    pass
