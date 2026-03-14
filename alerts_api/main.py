from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.providers import mock_alerts, mock_rapid7, mock_splunk, mock_tanium
from api.v1.database import engine, Base, create_database_if_not_exists
from api.v1.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database_if_not_exists(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Alerts API", version="0.1.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For Demo purposes, in PROD, set specific origins!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mock_alerts.router)
app.include_router(mock_rapid7.router)
app.include_router(mock_splunk.router)
app.include_router(mock_tanium.router)
