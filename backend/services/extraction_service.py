"""
Servicio de extracción de texto.

Convierte el contenido binario de un archivo (PDF, DOCX, TXT, MD) en
un string limpio que luego pasará al chunking + embeddings.

Las librerías de extracción son síncronas; las envolvemos en
`asyncio.to_thread` para no bloquear el event loop.
"""

import asyncio
import io
import logging

import pdfplumber
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


# MIME types soportados (debe coincidir con `Settings.allowed_mime_types`)
MIME_PDF = "application/pdf"
MIME_TEXT = "text/plain"
MIME_MARKDOWN = "text/markdown"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class ExtractionError(Exception):
    """Error al extraer texto de un archivo."""


# ============================================================
# Extractores específicos (sync)
# ============================================================
def _extract_pdf(data: bytes) -> str:
    """Extrae texto de un PDF usando pdfplumber."""
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_docx(data: bytes) -> str:
    """Extrae texto de un DOCX usando python-docx."""
    document = DocxDocument(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_plain(data: bytes) -> str:
    """Decodifica bytes como texto plano UTF-8 (TXT, MD)."""
    # Intenta UTF-8; si falla, intenta latin-1 como fallback razonable
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 falló al decodificar; intentando latin-1")
        return data.decode("latin-1", errors="replace")


# ============================================================
# API pública (async)
# ============================================================
async def extract_text(data: bytes, mime_type: str) -> str:
    """
    Extrae texto plano de un archivo según su MIME type.

    Lanza `ExtractionError` si:
      - el MIME no es soportado
      - la extracción falla
      - el resultado está vacío (archivo sin texto, p.ej. PDF solo imágenes)
    """
    def _do_extract() -> str:
        try:
            if mime_type == MIME_PDF:
                return _extract_pdf(data)
            elif mime_type == MIME_DOCX:
                return _extract_docx(data)
            elif mime_type in (MIME_TEXT, MIME_MARKDOWN):
                return _extract_plain(data)
            else:
                raise ExtractionError(f"MIME type no soportado: {mime_type}")
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Error extrayendo texto: {exc}") from exc

    text = await asyncio.to_thread(_do_extract)

    text = text.strip()
    if not text:
        raise ExtractionError(
            "El archivo no contiene texto extraíble "
            "(¿PDF escaneado sin OCR? ¿archivo vacío?)."
        )

    logger.info(
        "Extracción OK: mime=%s, %d caracteres",
        mime_type, len(text),
    )
    return text
