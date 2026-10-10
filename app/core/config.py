import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Geospatial File Measurement API"
    API_V1_STR: str = "/api"
    # Local SQLite fallback if nothing else provided
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./geospatial.db"
    
    # Validation settings
    MAX_UPLOAD_SIZE_MB: int = 50

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
