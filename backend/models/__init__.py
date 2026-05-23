"""
Paquete de modelos ORM.

Importa todos los modelos aquí para que:
1. Alembic los detecte en `target_metadata = Base.metadata`.
2. El resto del código pueda hacer `from models import User, Document, ...`.
"""

from models.chunk import Chunk
from models.conversation import Conversation
from models.document import Document, DocumentStatus
from models.message import Message, MessageRole
from models.user import User

__all__ = [
    "User",
    "Document",
    "DocumentStatus",
    "Chunk",
    "Conversation",
    "Message",
    "MessageRole",
]
