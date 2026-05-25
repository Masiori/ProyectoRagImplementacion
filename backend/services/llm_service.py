"""
Servicio LLM: cliente Ollama vía langchain-ollama.

Encapsula la comunicación con Ollama para aislar el resto del código de
cambios de API. Expone:
  - `generate(system_prompt, user_prompt) -> str`
  - `health_check() -> dict`
"""

import logging
from typing import Any

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMError(Exception):
    """Error genérico al invocar el LLM."""


class LLMService:
    """Wrapper sobre Ollama vía LangChain."""

    def __init__(self) -> None:
        logger.info(
            "Inicializando cliente Ollama: base_url=%s model=%s timeout=%ds",
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ollama_timeout_seconds,
        )
        self._llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            timeout=settings.ollama_timeout_seconds,
            # Temperatura baja para reducir creatividad (queremos respuestas
            # apegadas al contexto, no inventiva)
            temperature=0.2,
        )

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Genera una respuesta del LLM dado un system prompt y un user prompt.

        Lanza `LLMError` si Ollama no responde o devuelve algo inesperado.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = await self._llm.ainvoke(messages)
        except Exception as exc:
            logger.exception("Error invocando Ollama")
            raise LLMError(f"Error invocando el LLM: {exc}") from exc

        content = response.content
        if not isinstance(content, str) or not content.strip():
            raise LLMError("El LLM devolvió una respuesta vacía.")

        return content.strip()

    async def health_check(self) -> dict[str, Any]:
        """
        Verifica que Ollama responde y que el modelo configurado está cargado.

        Hace GET a {base_url}/api/tags y revisa que `ollama_model` aparezca.
        """
        url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama no responde: {exc}") from exc

        models = [m.get("name") for m in data.get("models", [])]
        target = settings.ollama_model
        # Ollama lista los modelos como "llama3.2:3b"; el matching es exacto
        is_loaded = target in models

        return {
            "ollama_url": settings.ollama_base_url,
            "model": target,
            "model_loaded": is_loaded,
            "available_models": models,
        }
