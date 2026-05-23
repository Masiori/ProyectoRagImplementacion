"""
Dependencias compartidas para FastAPI (DI).

En el Milestone 2 solo expone `get_db`. En milestones siguientes se
agregarán aquí:
  - `get_current_user` (Milestone 3): valida JWT y devuelve User
  - clientes de servicios externos (S3, embeddings, Ollama)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia que provee una `AsyncSession` por request.

    - Commit explícito si no hubo excepción.
    - Rollback automático si la excepción burbujeó al endpoint.
    - Cierre garantizado al final del request.

    Uso en un endpoint:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
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
