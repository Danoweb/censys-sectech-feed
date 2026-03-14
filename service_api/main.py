import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import alerts, sync, health
from api.v1.database import engine, Base, create_database_if_not_exists, SessionLocal
from api.v1.config import settings
from api.v1.services.sync_alerts import SyncAlerts


async def sync_loop():
    while True:
        db = SessionLocal()
        try:
            SyncAlerts(db).run_sync()
        except Exception as e:
            print(f"Sync failed: {e}")
        finally:
            db.close()

        await asyncio.sleep(settings.SYNC_INTERVAL_MINUTES * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database_if_not_exists(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    task = asyncio.create_task(sync_loop())
    yield
    task.cancel()


app = FastAPI(title="Service API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For Demo purposes, in PROD, set specific origins!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(alerts.router)
app.include_router(sync.router)
app.include_router(health.router)
