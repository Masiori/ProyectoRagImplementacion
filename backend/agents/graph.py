"""
Construcción del grafo del agente.

Topología:

    START
      │
      ▼
    receive_question
      │
      ▼
    retrieve_context
      │
      ▼
    evaluate_relevance
      │
   ┌──┴──┐  (arista condicional)
   ▼     ▼
generate_answer    reject_question
   │     │
   └──┬──┘
      ▼
    save_history
      │
      ▼
    END
"""

from langgraph.graph import END, StateGraph

from agents.nodes import AgentNodes
from agents.state import AgentState


def build_agent_graph(nodes: AgentNodes):
    """
    Construye y compila el grafo del agente.

    Recibe una instancia de `AgentNodes` con sus dependencias inyectadas
    (db, embedding_service, llm_service). Devuelve un grafo compilado
    listo para `await graph.ainvoke(initial_state)`.
    """
    builder = StateGraph(AgentState)

    # ----- Registrar nodos -----
    builder.add_node("receive_question", nodes.receive_question)
    builder.add_node("retrieve_context", nodes.retrieve_context)
    builder.add_node("evaluate_relevance", nodes.evaluate_relevance)
    builder.add_node("generate_answer", nodes.generate_answer)
    builder.add_node("reject_question", nodes.reject_question)
    builder.add_node("save_history", nodes.save_history)

    # ----- Entry point -----
    builder.set_entry_point("receive_question")

    # ----- Aristas lineales -----
    builder.add_edge("receive_question", "retrieve_context")
    builder.add_edge("retrieve_context", "evaluate_relevance")

    # ----- Arista condicional (la decisión clave del agente) -----
    builder.add_conditional_edges(
        "evaluate_relevance",
        nodes.route_after_evaluate,
        {
            "generate_answer": "generate_answer",
            "reject_question": "reject_question",
        },
    )

    # ----- Ambas ramas convergen en save_history -----
    builder.add_edge("generate_answer", "save_history")
    builder.add_edge("reject_question", "save_history")

    # ----- Fin -----
    builder.add_edge("save_history", END)

    return builder.compile()
