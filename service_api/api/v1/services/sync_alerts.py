from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy.orm import Session
from api.v1.models.alerts import Alert
from api.v1.models.sync import Sync
from api.v1.services.rapid7_client import Rapid7Client
from api.v1.services.tanium_client import TaniumClient
from api.v1.services.splunk_client import SplunkClient
from api.v1.config import settings


class SyncAlerts:

    def __init__(self, db: Session):
        self.db = db

    def get_last_successful_sync(self) -> Sync | None:
        return (
            self.db.query(Sync)
            .filter(Sync.sync_status == "success")
            .order_by(Sync.sync__at.desc())
            .first()
        )

    def is_sync_due(self) -> bool:
        last_sync = self.get_last_successful_sync()
        if not last_sync or not last_sync.sync__at:
            return True
        last_sync_at = last_sync.sync__at
        if last_sync_at.tzinfo is None:
            last_sync_at = last_sync_at.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(tz=timezone.utc) - last_sync_at
        return elapsed > timedelta(minutes=settings.SYNC_INTERVAL_MINUTES)

    def run_sync(self, use_safe_interval: bool = True) -> dict:
        if use_safe_interval and not self.is_sync_due():
            print("Last sync is within the interval — skipping.")
            return {"synced": False, "reason": "within interval"}
        
        print("Syncing — pulling alerts from alerts_api...")

        result = self.get_alerts()
        alerts = result.get("alerts", [])
        print(f"Fetched {len(alerts)} alerts — enriching...")

        enriched = []
        for raw in alerts:
            alert = Alert(
                alert_id=raw.get("alert_id", ""),
                alert_type=raw.get("alert_type", "unknown"),
                description=raw.get("description"),
                severity=raw.get("severity", "low"),
                source=raw.get("source"),
                hostname=raw.get("host"),
                ip_addressV4=raw.get("ip"),
            )
            source = (raw.get("source") or "").lower()
            try:
                if source == "rapid7":
                    alert = Rapid7Client().enrich(alert)
                elif source == "tanium":
                    alert = TaniumClient().enrich(alert)
                elif source == "splunk":
                    alert = SplunkClient().enrich(alert)
            except Exception as e:
                print(f"Enrichment failed for {source} alert {alert.alert_id}: {e}")
            enriched.append(alert)

        saved = 0
        for alert in enriched:
            try:
                self.db.add(alert)
                self.db.flush()
                saved += 1
            except Exception as e:
                print(f"Failed to save alert {alert.alert_id}: {e}")
                self.db.rollback()

        self.db.add(Sync(sync_status="success", sync__at=datetime.now(tz=timezone.utc)))
        self.db.commit()

        print(f"Sync complete. Saved {saved}/{len(enriched)} alerts.")
        return {"synced": True, "count": saved}

    def get_alerts(self, since: datetime | None = None) -> dict:
        last_sync = since or (
            self.get_last_successful_sync().sync__at
            if self.get_last_successful_sync()
            else datetime.fromtimestamp(0, tz=timezone.utc)
        )
        response = httpx.get(
            f"{settings.ALERTS_API_URL}/alerts",
            params={"since": last_sync.isoformat()},
        )
        response.raise_for_status()
        return response.json()
