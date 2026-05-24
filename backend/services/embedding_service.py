"""
Servicio de embeddings.

Carga el modelo `multilingual-e5-small` una sola vez (en el lifespan de
FastAPI) y expone dos métodos:

  - `embed_passages(texts)`: para indexar chunks (prefija 'passage: ')
  - `embed_query(text)`:     para buscar (prefija 'query: ')

Los prefijos son requisito del modelo e5; sin ellos la calidad cae
notablemente. La instancia del servicio queda en `app.state.embedding_service`
y se accede vía la dependencia `get_embedding_service`.
"""

import asyncio
import logging

from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Tamaño de batch al embeddear chunks
_BATCH_SIZE = 32


class EmbeddingService:
    """Wrapper sobre sentence-transformers para el modelo e5."""

    def __init__(self) -> None:
        logger.info(
            "Cargando modelo de embeddings: %s",
            settings.embedding_model,
        )
        self._model = SentenceTransformer(settings.embedding_model)

        # Sanity check: dimensión coincide con la columna Vector(N)
        actual_dim = self._model.get_sentence_embedding_dimension()
        if actual_dim != settings.embedding_dimension:
            raise RuntimeError(
                f"Mismatch de dimensión: el modelo produce {actual_dim}-dim "
                f"pero EMBEDDING_DIMENSION={settings.embedding_dimension}. "
                f"Revisa la config o cambia el modelo."
            )

        logger.info(
            "Modelo de embeddings cargado (dim=%d)",
            settings.embedding_dimension,
        )

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------
    async def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """
        Embebe una lista de chunks para indexación.
        Aplica el prefijo 'passage: ' que e5 requiere para textos a indexar.
        """
        prefixed = [f"passage: {t}" for t in texts]
        return await asyncio.to_thread(self._encode_batched, prefixed)

    async def embed_query(self, text: str) -> list[float]:
        """
        Embebe una pregunta de usuario para retrieval.
        Aplica el prefijo 'query: ' que e5 requiere para queries.
        """
        prefixed = f"query: {text}"
        result = await asyncio.to_thread(self._encode_batched, [prefixed])
        return result[0]

    # ------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------
    def _encode_batched(self, texts: list[str]) -> list[list[float]]:
        """Codifica en batches para no saturar memoria con textos largos."""
        vectors = self._model.encode(
            texts,
            batch_size=_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # e5 funciona mejor normalizado
        )
        return vectors.tolist()
