from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database_if_not_exists(database_url: str):
    if not database_url:
        return
    
    # Extract database name from URL
    # mysql+pymysql://user:pass@host/dbname -> dbname
    database_name = database_url.split('/')[-1]
    
    # Create connection to MySQL server (without database)
    server_url = database_url.rsplit('/', 1)[0]  # Remove database name
    
    try:
        engine = create_engine(server_url)
        with engine.connect() as connection:
            # Create database if it doesn't exist
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database_name}`"))
            connection.commit()
            print(f"Database '{database_name}' created if it did not already exist.")
    except Exception as e:
        print(f"Could not create database: {e}")