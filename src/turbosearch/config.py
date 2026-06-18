from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://turbosearch:turbosearch@localhost:5432/turbosearch"
    embedding_provider: str = "qwen"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_dim: int = 1024
    index_dim: int = 256
    index_version: int = 1
    vector_index_path: str = ".turbosearch/vectors.json"
    overview_mode: str = "llm"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen3:0.6b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
