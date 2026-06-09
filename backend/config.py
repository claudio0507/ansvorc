from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:///./sinalys.db"
    APP_NAME: str = "Sinalys"
    APP_VERSION: str = "1.0.0"
    # False por padrão; testes e dev local definem DEBUG=true no .env
    DEBUG: bool = False
    JWT_SECRET: str = "sinalys-dev-secret-mude-em-producao"

    def __init__(self, **data):
        super().__init__(**data)
        _placeholder = "sinalys-dev-secret-mude-em-producao"
        if self.JWT_SECRET == _placeholder and not self.DEBUG:
            import warnings

            warnings.warn(
                "JWT_SECRET está com o valor padrão inseguro. "
                "Defina JWT_SECRET no ambiente ou em .env antes de iniciar em produção.",
                stacklevel=2,
            )


settings = Settings()
