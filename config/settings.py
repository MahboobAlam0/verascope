"""
Centralized pipeline configuration.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    groq_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    llm_provider: str | None = Field(default=None)
    anthropic_model: str | None = Field(default=None)
    openai_model: str | None = Field(default=None)
    groq_model: str | None = Field(default=None)
    gemini_model: str | None = Field(default=None)

    input_dir: Path = Field(default=Path("data/input"))
    output_dir: Path = Field(default=Path("data/output"))

    log_level: str = Field(default="INFO")


settings = Settings()
