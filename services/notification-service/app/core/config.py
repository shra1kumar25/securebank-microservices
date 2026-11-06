from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SecureBank Notification Service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./notification.db"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    JWT_SECRET_KEY: str = "local-development-secret-change-before-deployment"
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
