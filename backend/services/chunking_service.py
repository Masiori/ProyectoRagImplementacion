"""
Servicio de chunking.

Divide texto largo en fragmentos manejables que luego se embedean.
Usa `RecursiveCharacterTextSplitter` de LangChain con separadores
jerárquicos: primero intenta cortar por párrafos (\\n\\n), luego por
líneas, oraciones, palabras, y por último por carácter.

Configurable vía settings:
  - `chunk_size`: tamaño objetivo en caracteres (default 800)
  - `chunk_overlap`: solapamiento entre chunks consecutivos (default 150)
"""

import asyncio
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================
# Splitter (instancia única reutilizable)
# ============================================================
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    length_function=len,
    is_separator_regex=False,
    separators=["\n\n", "\n", ". ", " ", ""],
)


async def chunk_text(text: str) -> list[str]:
    """
    Divide el texto en chunks. Devuelve lista de strings.

    La operación es CPU-bound pero rápida; aún así la mandamos a un
    thread para no afectar el event loop si el texto es grande.
    """
    chunks = await asyncio.to_thread(_splitter.split_text, text)
    # Filtrar chunks vacíos (raros pero posibles si el texto tiene
    # secciones de separadores puros)
    chunks = [c.strip() for c in chunks if c.strip()]
    logger.info("Chunking OK: %d chunks generados", len(chunks))
    return chunks
