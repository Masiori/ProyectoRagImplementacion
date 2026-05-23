"""
Modelo `User`.

Representa al usuario autenticado vía Cognito. La fuente de verdad de
la identidad es `cognito_sub` (el claim `sub` del JWT). En el Milestone 3
se creará automáticamente una fila aquí la primera vez que un usuario
inicie sesión.
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.conversation import Conversation
    from models.document import Document


class User(Base, UUIDMixin, TimestampMixin):
    """Usuario de la aplicación."""

    __tablename__ = "users"

    # ------------------------------------------------------------
    # Identidad
    # ------------------------------------------------------------
    # `cognito_sub` es el UUID que Cognito asigna a cada usuario en su
    # User Pool. Es estable y único sin importar el proveedor de login
    # (email/password o Google federado).
    cognito_sub: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),  # RFC 5321: máximo legal de un email
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------
    # Proveedor de autenticación
    # ------------------------------------------------------------
    # Valores esperados: 'cognito' (email/password) o 'google'.
    # No es un enum a nivel BD para poder agregar proveedores sin migrar.
    auth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="cognito",
        server_default="cognito",
    )

    # ------------------------------------------------------------
    # Relaciones inversas
    # ------------------------------------------------------------
    # User → Document: RESTRICT (no se borran usuarios con documentos).
    # User → Conversation: RESTRICT.
    documents: Mapped[list["Document"]] = relationship(
        back_populates="user",
        passive_deletes="all",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        passive_deletes="all",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} provider={self.auth_provider}>"
