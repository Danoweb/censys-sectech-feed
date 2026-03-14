from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.v1.database import get_db
from api.v1.models.alerts import Alert

router = APIRouter(tags=["alerts"])


@router.get("/alerts")
def get_alerts(
    since: Optional[datetime] = Query(None, description="ISO8601 timestamp — return alerts with created_at >= this value"),
    hostname: Optional[str] = Query(None, description="Filter by hostname"),
    source: Optional[str] = Query(None, description="Filter by source"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
):
    query = db.query(Alert)

    if since:
        query = query.filter(Alert.created_at >= since)
    if hostname:
        query = query.filter(Alert.hostname == hostname)
    if source:
        query = query.filter(Alert.source == source)
    if severity:
        query = query.filter(Alert.severity == severity)

    alerts = query.order_by(Alert.created_at.asc()).all()

    return {
        "count": len(alerts),
        "filters": {
            "since": since.isoformat() if since else None,
            "hostname": hostname,
            "source": source,
            "severity": severity,
        },
        "alerts": [
            {
                "id": a.id,
                "alert_id": a.alert_id,
                "alert_type": a.alert_type,
                "description": a.description,
                "severity": a.severity,
                "source": a.source,
                "hostname": a.hostname,
                "ip_addressV4": a.ip_addressV4,
                "ip_addressV6": a.ip_addressV6,
                "port": a.port,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in alerts
        ],
    }
