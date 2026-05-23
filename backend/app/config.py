"""
Configuración centralizada de la aplicación.
Lee variables de entorno desde el archivo .env (gracias a pydantic-settings).

Las variables que aún no se usan en el Milestone 1 están comentadas;
se irán habilitando en los milestones correspondientes.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global tipada de la aplicación."""

    # ------------------------------------------------------------
    # Aplicación
    # ------------------------------------------------------------
    app_name: str = "agente-gastronomia-colombiana"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ------------------------------------------------------------
    # Base de datos (Milestone 2+)
    # Por ahora la cargamos pero no la usamos.
    # ------------------------------------------------------------
    database_url: str = (
        "postgresql+asyncpg://agente_user:agente_password@postgres:5432/agente_db"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True

    # ------------------------------------------------------------
    # Ollama (Milestone 5+)
    # ------------------------------------------------------------
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"

    # ------------------------------------------------------------
    # Embeddings (Milestone 4+)
    # ------------------------------------------------------------
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dimension: int = 384

    # ------------------------------------------------------------
    # RAG (Milestone 5+)
    # ------------------------------------------------------------
    similarity_threshold: float = 0.70
    top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 150

    # ------------------------------------------------------------
    # AWS Cognito (Milestone 3+)
    # ------------------------------------------------------------
    cognito_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""

    # ------------------------------------------------------------
    # AWS S3 (Milestone 4+)
    # ------------------------------------------------------------
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # ------------------------------------------------------------
    # CORS (Milestone 6+)
    # ------------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte la cadena separada por comas en una lista."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Devuelve la instancia única de settings.
    El @lru_cache garantiza que .env se lee una sola vez.
    """
    return Settings()
