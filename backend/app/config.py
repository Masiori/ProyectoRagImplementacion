"""
Configuración centralizada de la aplicación.
Lee variables de entorno desde el archivo .env (gracias a pydantic-settings).
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
    ollama_timeout_seconds: int = 60                # Configurable

    # ------------------------------------------------------------
    # Embeddings (Milestone 4+)
    # ------------------------------------------------------------
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dimension: int = 384

    # ------------------------------------------------------------
    # RAG / Chunking (Milestone 4+ y 5+)
    # ------------------------------------------------------------
    similarity_threshold: float = 0.70
    top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 150

    # ------------------------------------------------------------
    # Chat (Milestone 5+)
    # ------------------------------------------------------------
    history_max_messages: int = 6                   # Últimos N mensajes en el prompt
    max_question_length: int = 800                  # Longitud máx. de pregunta (chars)

    # ------------------------------------------------------------
    # Upload de documentos (Milestone 4+)
    # ------------------------------------------------------------
    max_upload_size_bytes: int = 20_971_520
    allowed_mime_types: str = (
        "application/pdf,"
        "text/plain,"
        "text/markdown,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    @property
    def allowed_mime_types_list(self) -> list[str]:
        return [m.strip() for m in self.allowed_mime_types.split(",") if m.strip()]

    # ------------------------------------------------------------
    # AWS Cognito (Milestone 3+)
    # ------------------------------------------------------------
    cognito_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""

    @property
    def cognito_issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )

    @property
    def cognito_jwks_url(self) -> str:
        return f"{self.cognito_issuer}/.well-known/jwks.json"

    @property
    def cognito_is_configured(self) -> bool:
        return bool(self.cognito_user_pool_id and self.cognito_app_client_id)

    # ------------------------------------------------------------
    # AWS S3 (Milestone 4+)
    # ------------------------------------------------------------
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    @property
    def s3_is_configured(self) -> bool:
        return bool(
            self.aws_s3_bucket
            and self.aws_access_key_id
            and self.aws_secret_access_key
        )

    # ------------------------------------------------------------
    # CORS (Milestone 6+)
    # ------------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
