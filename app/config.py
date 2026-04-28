from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    comfy_base_url: str = Field(alias="COMFY_BASE_URL")
    comfy_ws_url: str = Field(alias="COMFY_WS_URL")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(alias="OPENROUTER_BASE_URL")
    agent_model: str = Field(alias="AGENT_MODEL")
    openrouter_http_referer: str = Field(default="http://localhost", alias="OPENROUTER_HTTP_REFERER")
    openrouter_app_title: str = Field(default="comfy-agent-mvp", alias="OPENROUTER_APP_TITLE")

    request_timeout: int = Field(default=120, alias="REQUEST_TIMEOUT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()