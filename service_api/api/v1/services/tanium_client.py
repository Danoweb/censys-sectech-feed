import httpx
from api.v1.models.alerts import Alert
from api.v1.utils.translate import translate
from api.v1.config import settings


class TaniumClient:

    def __init__(self):
        self._base_url = f"{settings.ALERTS_API_URL}/api/v1/tanium"

    def _get_endpoint(self, hostname: str) -> dict | None:
        response = httpx.get(
            f"{self._base_url}/tanium_threat_response",
        )
        response.raise_for_status()
        edges = response.json().get("data", {}).get("endpoints", {}).get("edges", [])
        # Find the node matching the hostname, fall back to first result
        for edge in edges:
            node = edge.get("node", {})
            if hostname and node.get("name", "").lower() == hostname.lower():
                return node
        return edges[0].get("node") if edges else None

    def _get_alerts(self, hostname: str) -> dict | None:
        response = httpx.get(
            f"{self._base_url}/get_alerts",
            params={"hostname": hostname},
        )
        response.raise_for_status()
        alerts = response.json().get("data", {}).get("alerts", [])
        return alerts[0] if alerts else None

    def enrich(self, alert: Alert) -> Alert:
        endpoint = self._get_endpoint(alert.hostname)
        if not endpoint:
            return alert

        tanium_alert = self._get_alerts(alert.hostname)
        if not tanium_alert:
            return alert

        obj = {"endpoint": endpoint, "alert": tanium_alert}

        mapping = {
            "alert_id":    lambda r: alert.alert_id,
            "alert_type":  lambda r: r("alert.Intel Type") or alert.alert_type,
            "description": lambda r: (
                f"{r('alert.Intel Name')} — {r('alert.Intel Labels')}"
                if r("alert.Intel Name") else alert.description
            ),
            "severity":    lambda r: alert.severity,
            "source":      lambda r: "Tanium",
            "hostname":    "endpoint.name",
            "ip_addressV4": "endpoint.ipAddress",
            "port":        "alert.MatchDetails.match.properties.remote_port",
        }

        return translate(obj, mapping)
