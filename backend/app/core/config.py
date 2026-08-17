from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    sqlite_path: str = "./data/eagleeye.db"

    qdrant_path: str = "./data/qdrant"
    qdrant_collection: str = "face_embeddings"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    media_root: str = "./media"


@lru_cache
def get_settings() -> Settings:
    return Settings()
