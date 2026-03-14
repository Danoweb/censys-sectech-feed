import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://danomock:danomock@alerts_db:3306/alerts_mock")
    ALERTS_API_URL: str = os.getenv("ALERTS_API_URL", "http://alerts_api:8000")
    SYNC_INTERVAL_MINUTES: int = os.getenv("SYNC_INTERVAL_MINUTES", 60)

settings = Settings()
