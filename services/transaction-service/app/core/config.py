from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SecureBank Transaction Service"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./transaction.db"

    JWT_SECRET_KEY: str = "local-development-secret-change-before-deployment"
    JWT_ALGORITHM: str = "HS256"

    ACCOUNT_SERVICE_URL: str = "http://localhost:8002"

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
