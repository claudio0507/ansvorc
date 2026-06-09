from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:///./sinalys.db"
    APP_NAME: str = "Sinalys"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    JWT_SECRET: str = "sinalys-dev-secret-mude-em-producao"


settings = Settings()
