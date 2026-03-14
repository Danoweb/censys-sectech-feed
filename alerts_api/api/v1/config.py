import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://danomock:danomock@alerts_db:3306/alerts_mock")

settings = Settings()
