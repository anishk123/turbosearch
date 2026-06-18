from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://turbosearch:turbosearch@localhost:5432/turbosearch"
    embedding_dim: int = 384
    overview_mode: str = "extractive"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

