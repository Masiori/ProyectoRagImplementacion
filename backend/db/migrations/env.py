"""
env.py de Alembic con soporte async.

Cómo funciona:
1. Importamos `Base.metadata` con todos los modelos.
2. Leemos `DATABASE_URL` del entorno y la inyectamos en la config de Alembic.
3. Creamos un AsyncEngine.
4. `connection.run_sync(do_run_migrations)` da a Alembic una vista
   síncrona sobre la conexión asíncrona, lo cual permite que su API
   síncrona (autogenerate, etc.) funcione sin cambios.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ------------------------------------------------------------
# Imports del proyecto
# ------------------------------------------------------------
# Importar Base y forzar el import de TODOS los modelos para que
# autogenerate los detecte vía Base.metadata.
from db.base import Base
import models  # noqa: F401  ← Importa __init__.py que registra todo

# ------------------------------------------------------------
# Configuración Alembic
# ------------------------------------------------------------
config = context.config

# Configura logging según alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inyecta la URL desde el entorno (no la hardcodeamos en alembic.ini)
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL no está definida en el entorno. "
        "Asegúrate de tener un .env válido o de exportar la variable."
    )
config.set_main_option("sqlalchemy.url", database_url)

# Metadatos que Alembic comparará contra la BD real
target_metadata = Base.metadata


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """
    Función SÍNCRONA. Alembic la invocará con una conexión sincrónica
    obtenida por `run_sync` desde un AsyncConnection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,             # Detecta cambios de tipo de columna
        compare_server_default=True,   # Detecta cambios en defaults SQL
        # Importante para que detecte el tipo Vector correctamente
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------
# Modo offline
# ------------------------------------------------------------
def run_migrations_offline() -> None:
    """Genera SQL puro sin conectarse a la BD (útil para revisar)."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------
# Modo online (el normal)
# ------------------------------------------------------------
async def run_async_migrations() -> None:
    """Crea el AsyncEngine y delega la ejecución sincrónica vía run_sync."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point del modo online: corre el event loop una vez."""
    asyncio.run(run_async_migrations())


# ------------------------------------------------------------
# Punto de entrada
# ------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
