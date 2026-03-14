import httpx
from api.v1.models.alerts import Alert
from api.v1.utils.translate import translate
from api.v1.config import settings


class Rapid7Client:

    def __init__(self):
        self._base_url = f"{settings.ALERTS_API_URL}/api/v1/rapid7"

    def _search_assets(self, hostname: str) -> dict | None:
        response = httpx.post(
            f"{self._base_url}/search_assets",
            json={"hostname": hostname},
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return data[0] if data else None

    def _search_alerts(self, asset_rrn: str) -> dict | None:
        response = httpx.post(
            f"{self._base_url}/search_alerts",
            json={"asset_rrn": asset_rrn},
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return data[0] if data else None

    def enrich(self, alert: Alert) -> Alert:
        if not alert.hostname:
            return alert

        asset = self._search_assets(alert.hostname)
        if not asset:
            return alert

        alert_data = self._search_alerts(asset.get("rrn", ""))
        if not alert_data:
            return alert

        # Merge both responses into a single object for the translator
        obj = {"asset": asset, "alert": alert_data}

        mapping = {
            "alert_id":    lambda r: alert.alert_id,
            "alert_type":  lambda r: r("alert.event_type") or alert.alert_type,
            "description": lambda r: (
                f"{r('alert.event_type')} — {r('alert.command_line')}"
                if r("alert.command_line") else alert.description
            ),
            "severity":    lambda r: alert.severity,
            "source":      lambda r: "Rapid7",
            "hostname":    "asset.host_name",
            "ip_addressV4": "asset.ip_address",
            "port":        "alert.remote_port",
        }

        return translate(obj, mapping)
