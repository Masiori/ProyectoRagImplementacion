# Backend — Agente RAG Gastronomía Colombiana

API REST construida con **FastAPI** que expone los endpoints del chat, gestión de documentos y autenticación. Aloja el agente **LangGraph** y se conecta a **PostgreSQL + pgvector** (vector store) y a **Ollama** (LLM local).

> **Estado actual:** Milestone 1 — solo `/health` está activo. El resto se construirá en milestones siguientes.

---

## Estructura

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entrypoint FastAPI
│   └── config.py            # Settings con pydantic-settings
├── agents/                  # LangGraph (Milestone 5)
├── services/                # Lógica de negocio (Milestones 2-5)
├── controllers/             # Routers FastAPI (Milestones 2-5)
├── models/                  # SQLAlchemy (Milestone 2)
├── schemas/                 # Pydantic (Milestone 2+)
├── db/                      # Sesión y migraciones
│   └── init/
│       └── 01-enable-pgvector.sql
├── vectorstore/
├── tests/
├── Dockerfile
├── .dockerignore
└── requirements.txt
```

---

## Ejecutar el backend

### Opción A — Con docker-compose (recomendado)

Desde la raíz del repo:

```bash
docker compose up -d backend
docker compose logs -f backend
```

### Opción B — Localmente con venv

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Necesita Postgres y Ollama corriendo aparte (puede ser desde docker compose):
# docker compose up -d postgres ollama

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Endpoints disponibles (Milestone 1)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Información básica |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (OpenAPI) |
| GET | `/redoc` | ReDoc |

---

## Próximos milestones

- **Milestone 2:** SQLAlchemy + Alembic, modelos `User`, `Document`, `Chunk`, `Conversation`.
- **Milestone 3:** Validación JWT de Cognito y dependencia `get_current_user`.
- **Milestone 4:** Servicios de documento, embedding, S3, y endpoints `/documents`.
- **Milestone 5:** Grafo LangGraph completo y endpoint `/chat`.

---

## Convenciones

- **Tipado:** usar type hints en todas las funciones.
- **Async:** todo IO (BD, Ollama, S3) es async.
- **Imports:** absolutos desde la raíz (`from app.config import ...`).
- **Configuración:** todo via `pydantic-settings`. No hardcodear secretos.
