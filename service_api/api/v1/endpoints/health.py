from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.v1.database import get_db
from api.v1.models.sync import Sync

router = APIRouter(tags=["health"])

DEGRADED_SYNC_THRESHOLD_MINUTES = 10


@router.get("/health")
def health(db: Session = Depends(get_db)):
    # Database connectivity
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    # Last successful sync
    last_success = (
        db.query(Sync)
        .filter(Sync.sync_status == "success")
        .order_by(Sync.sync__at.desc())
        .first()
    )

    # Recent ingestion errors (failed syncs since last success)
    since = last_success.sync__at if last_success else datetime.fromtimestamp(0, tz=timezone.utc)
    recent_errors = (
        db.query(Sync)
        .filter(Sync.sync_status != "success", Sync.sync__at > since)
        .order_by(Sync.sync__at.desc())
        .limit(5)
        .all()
    )

    # Determine overall status
    if not db_ok:
        status = "down"
    elif recent_errors or not last_success:
        status = "degraded"
    else:
        last_sync_at = last_success.sync__at
        if last_sync_at.tzinfo is None:
            last_sync_at = last_sync_at.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(tz=timezone.utc) - last_sync_at
        status = "degraded" if elapsed > timedelta(minutes=DEGRADED_SYNC_THRESHOLD_MINUTES) else "ok"

    return {
        "status": status,
        "database": "connected" if db_ok else "unreachable",
        "last_successful_sync": last_success.sync__at.isoformat() if last_success else None,
        "recent_ingestion_errors": [
            {
                "sync_status": e.sync_status,
                "sync_at": e.sync__at.isoformat() if e.sync__at else None,
            }
            for e in recent_errors
        ],
    }
