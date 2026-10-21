"""Application Configuration & Environment Settings."""

import secrets
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration validated through Pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AitMate"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Network Security: Strictly loopback
    HOST: str = Field(default="127.0.0.1", alias="AITMATE_BACKEND_HOST")
    PORT: int = Field(default=8000, alias="AITMATE_BACKEND_PORT")

    # Ephemeral or configured Bearer token for local API authentication
    API_TOKEN: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        alias="AITMATE_API_TOKEN",
    )

    # Permitted desktop UI origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "tauri://localhost",
        "http://tauri.localhost",
    ]

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./aitmate.db",
        alias="AITMATE_DATABASE_URL",
    )

    # Provider & Automation Settings
    AI_PROVIDER: str = Field(default="mock", alias="AITMATE_AI_PROVIDER")
    OLLAMA_BASE_URL: str = Field(
        default="http://127.0.0.1:11434",
        alias="AITMATE_OLLAMA_BASE_URL",
    )
    OLLAMA_MODEL: str = Field(
        default="llama3.2:latest",
        alias="AITMATE_OLLAMA_MODEL",
    )
    # Groq Cloud Provider Settings
    GROQ_API_KEY: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        alias="AITMATE_GROQ_MODEL",
    )
    GROQ_BASE_URL: str = Field(
        default="https://api.groq.com/openai/v1",
        alias="AITMATE_GROQ_BASE_URL",
    )
    BROWSER_HEADLESS: bool = Field(default=False, alias="AITMATE_BROWSER_HEADLESS")
    ALLOWED_DOMAINS: str = Field(
        default="wikipedia.org,github.com,gitlab.com,python.org",
        alias="AITMATE_ALLOWED_DOMAINS",
    )
    AUDIT_LOG_PATH: str = Field(
        default="./aitmate_audit.log",
        alias="AITMATE_AUDIT_LOG_PATH",
    )

    @field_validator("HOST")
    @classmethod
    def validate_loopback_host(cls, v: str) -> str:
        """Enforce that the server binds exclusively to loopback interfaces."""
        allowed = {"127.0.0.1", "localhost", "::1"}
        if v not in allowed:
            raise ValueError(
                f"Security violation: AitMate backend must bind strictly to a loopback interface ({allowed}), not '{v}'"
            )
        return v

    def get_allowed_domain_list(self) -> List[str]:
        """Return allowed domains as a clean list of lowercased hostnames."""
        return [d.strip().lower() for d in self.ALLOWED_DOMAINS.split(",") if d.strip()]


# Global cached settings instance
settings = Settings()
