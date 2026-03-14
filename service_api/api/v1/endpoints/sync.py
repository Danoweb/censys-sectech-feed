from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.v1.database import get_db
from api.v1.services.sync_alerts import SyncAlerts

router = APIRouter(tags=["sync"])


@router.post("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    return SyncAlerts(db).run_sync(use_safe_interval=False)
