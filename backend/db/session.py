"""
Sesión y motor de base de datos.

Aquí vive el AsyncEngine único de la aplicación y el sessionmaker que
produce sesiones para cada request. La función `get_db` que entrega
sesiones a los endpoints vive en `app/dependencies.py`.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()


# ------------------------------------------------------------
# Motor asincrónico
# ------------------------------------------------------------
# `pool_pre_ping=True` evita errores por conexiones colgadas
# (problema clásico tras un reinicio de Postgres o un idle largo).
# `echo` muestra el SQL generado en logs cuando debug=True.
# ------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=settings.db_pool_pre_ping,
    future=True,
)


# ------------------------------------------------------------
# Factory de sesiones
# ------------------------------------------------------------
# `expire_on_commit=False` impide que los objetos se vuelvan "stale"
# después de un commit, lo cual es lo deseado en APIs web.
# ------------------------------------------------------------
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
