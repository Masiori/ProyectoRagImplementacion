"""
Estado del agente LangGraph.

`AgentState` es el TypedDict que fluye entre los 6 nodos del grafo.
LangGraph hace un merge automático: cada nodo devuelve un dict parcial
con los campos que actualiza, y LangGraph lo fusiona con el estado actual.
"""

import uuid
from dataclasses import dataclass
from typing import Optional, TypedDict

from services.vector_service import RetrievedChunk


@dataclass
class HistoryMessage:
    """Mensaje pasado del historial conversacional, para incluir en el prompt."""

    role: str        # 'user' | 'assistant'
    content: str


class AgentState(TypedDict, total=False):
    """
    Estado del agente. Marcado `total=False` para que cada nodo pueda
    devolver solo los campos que actualiza, sin fallar por los faltantes.
    """

    # ----- Input (se setea al inicio) -----
    question: str
    user_id: uuid.UUID
    conversation_id: uuid.UUID
    history: list[HistoryMessage]

    # ----- Resultado del retrieval -----
    retrieved_chunks: list[RetrievedChunk]
    best_similarity: float

    # ----- Decisión -----
    has_sufficient_context: bool
    rejection_reason: Optional[str]

    # ----- Output -----
    answer: str
    assistant_message_id: Optional[uuid.UUID]   # id del Message de respuesta guardado
