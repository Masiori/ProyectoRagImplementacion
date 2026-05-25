"""
Prompts del agente RAG.

Constantes:
  - `SYSTEM_PROMPT`: instrucciones de comportamiento del asistente.
  - `CANONICAL_REJECTION`: respuesta exacta cuando no hay contexto suficiente
    (texto literal del enunciado del trabajo).

Funciones:
  - `build_user_prompt(question, retrieved_chunks, history)`: arma el mensaje
    "user" que se envía al LLM con CONTEXTO + HISTORIAL + PREGUNTA.
"""

from agents.state import HistoryMessage
from services.vector_service import RetrievedChunk


# ============================================================
# Constantes
# ============================================================
SYSTEM_PROMPT = """Eres un asistente experto en gastronomía colombiana. Respondes preguntas usando ÚNICAMENTE la información presente en el CONTEXTO entregado por el sistema.

Reglas estrictas que debes cumplir SIEMPRE:

1. NO uses información que no esté explícitamente en el CONTEXTO.
2. NO inventes recetas, ingredientes, fechas, regiones, ni cualquier otro dato.
3. Si la información necesaria NO está en el CONTEXTO, responde EXACTAMENTE con esta frase y nada más:
   "No tengo suficiente información en mi base de conocimiento para responder esa pregunta."
4. Responde siempre en español, de forma clara y concisa.
5. Cuando sea relevante, menciona el documento del que proviene la información (lo verás como "Fuente: <nombre>" en el CONTEXTO).
6. NO uses frases como "según mi conocimiento", "creo que" o "probablemente". Usa solo afirmaciones basadas en el CONTEXTO.
7. Si la pregunta hace referencia al historial reciente de la conversación, úsalo para entender el contexto, pero la respuesta debe seguir basándose en el CONTEXTO.
"""


CANONICAL_REJECTION = (
    "No tengo suficiente información en mi base de conocimiento "
    "para responder esa pregunta."
)


# ============================================================
# Builders
# ============================================================
def build_user_prompt(
    question: str,
    retrieved_chunks: list[RetrievedChunk],
    history: list[HistoryMessage],
) -> str:
    """
    Construye el mensaje 'user' que se envía al LLM.

    Estructura:
        CONTEXTO:
        [Fuente: doc1.pdf]
        <chunk 1>

        [Fuente: doc2.pdf]
        <chunk 2>

        HISTORIAL DE LA CONVERSACIÓN (si aplica):
        Usuario: ...
        Asistente: ...

        PREGUNTA DEL USUARIO:
        <question>
    """
    # --- CONTEXTO ---
    context_parts = []
    for chunk in retrieved_chunks:
        context_parts.append(
            f"[Fuente: {chunk.filename}]\n{chunk.content.strip()}"
        )
    context_block = "\n\n".join(context_parts) if context_parts else "(sin contexto)"

    # --- HISTORIAL (opcional) ---
    history_block = ""
    if history:
        lines = []
        for msg in history:
            who = "Usuario" if msg.role == "user" else "Asistente"
            lines.append(f"{who}: {msg.content.strip()}")
        history_block = (
            "\n\nHISTORIAL DE LA CONVERSACIÓN (más reciente al final):\n"
            + "\n".join(lines)
        )

    return (
        f"CONTEXTO:\n{context_block}"
        f"{history_block}"
        f"\n\nPREGUNTA DEL USUARIO:\n{question.strip()}"
    )
