from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SecureBank Auth Service"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./auth.db"

    JWT_SECRET_KEY: str = "dev-only-change-this-secret-before-deployment"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
