import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Configurações da aplicação.
    """
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(..., env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(..., env="REFRESH_TOKEN_EXPIRE_MINUTES")

    ADMIN_NAME: str = Field(..., env="ADMIN_NAME")
    ADMIN_EMAIL: str = Field(..., env="ADMIN_EMAIL")
    ADMIN_PASSWORD: str = Field(..., env="ADMIN_PASSWORD")
    
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    REDIS_HOST: str = Field(..., env="REDIS_HOST")
    REDIS_PORT: int = Field(..., env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(..., env="REDIS_PASSWORD")
    
    KAFKA_BROKERS: str = Field(..., env="KAFKA_BROKERS")
    KAFKA_USER_REGISTRATION_TOPIC: str = Field(..., env="KAFKA_USER_REGISTRATION_TOPIC")
    
    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: int = Field(..., env="SMTP_PORT")

    AI_CONFIDENCE_THRESHOLD: float = Field(..., env="AI_CONFIDENCE_THRESHOLD")
    class Config:
        # env_file = ".env"
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()