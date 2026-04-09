from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/carlease"
    GOOGLE_API_KEY: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    NHTSA_API_BASE: str = "https://vpic.nhtsa.dot.gov/api"
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()