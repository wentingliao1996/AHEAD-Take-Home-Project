# core/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "AHEAD Take Home Project"
    API_V1_STR: str = "/api/v1"

    # DB
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_MB: int = 1000

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")

settings = Settings()

if __name__ == "__main__":
    print(settings.dict())