from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de Datos
    DATABASE_URL: str = "postgresql+asyncpg://cotia_user:cotia_pass@localhost:5432/cotia"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # Entorno
    ENVIRONMENT: str = "development"

    # JWT
    JWT_SECRET_KEY: str = "change_this_secret_key_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Bcrypt
    BCRYPT_COST_FACTOR: int = 12

    # Negocio
    MARGEN_COMPETENCIA: float = 5.0
    TIENDA_PROPIA: str = "AV Electronics"
    MAX_FILE_SIZE_MB: int = 25
    MAX_PREGUNTAS_SESION: int = 2

    # Gemini Vision API
    GEMINI_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
