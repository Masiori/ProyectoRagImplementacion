
"""
Schemas Pydantic para User.
 
Aquí solo el modelo de respuesta. Como los usuarios se crean automáticamente
desde el JWT, no hay schema de "create" expuesto a clientes.
"""
 
from datetime import datetime
from uuid import UUID
 
from pydantic import BaseModel, ConfigDict
 
 
class UserResponse(BaseModel):
    """Forma del usuario tal como se devuelve por la API."""
 
    id: UUID
    # `email` como str (no EmailStr): el email viene del JWT de Cognito,
    # que ya validó su formato antes de emitir el token. Re-validar acá
    # sumaría una dependencia (email-validator) sin valor real.
    email: str
    auth_provider: str
    created_at: datetime
    updated_at: datetime
 
    # from_attributes=True permite construir el schema desde un objeto
    # SQLAlchemy directamente (sin convertir a dict manualmente).
    model_config = ConfigDict(from_attributes=True)
 
