"""Server configuration using Pydantic Settings"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(default="sqlite:///./aetheredge.db", alias="DATABASE_URL")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # Node management
    node_timeout: int = Field(default=30, alias="NODE_TIMEOUT")  # seconds before marking OFFLINE
    heartbeat_grace: int = Field(default=5, alias="HEARTBEAT_GRACE")  # grace period

    # API
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"], alias="CORS_ORIGINS")


settings = Settings()