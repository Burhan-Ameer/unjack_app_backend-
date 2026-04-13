from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    fcm_server_key: str
    log_level: str = "INFO"
    sqlalchemy_echo: bool = False
    auth_rate_limit_per_minute: int = 15
    auth_rate_limit_window_seconds: int = 60
    redis_url: str = "redis://redis:6379/0"
    rate_limit_key_prefix: str = "rate_limit:auth"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        valid = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        normalized = value.upper()
        if normalized not in valid:
            raise ValueError(f"Invalid LOG_LEVEL '{value}'. Use one of: {', '.join(sorted(valid))}")
        return normalized

settings = Settings()
