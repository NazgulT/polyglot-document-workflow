# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # Ingestion limits
    max_upload_bytes: int = 20 * 1024 * 1024      # 20 MB hard limit
    allowed_mime_types: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]

    # Storage — where extracted text files are written
    # In production: swap for an S3 bucket path
    extracted_text_dir: str = "/tmp/extracted_texts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()