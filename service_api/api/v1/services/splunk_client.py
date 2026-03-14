import httpx
from api.v1.models.alerts import Alert
from api.v1.utils.translate import translate
from api.v1.config import settings


class SplunkClient:

    def __init__(self):
        self._base_url = f"{settings.ALERTS_API_URL}/api/v1/splunk"

    def _search_alerts(self) -> dict | None:
        response = httpx.post(
            f"{self._base_url}/search_alerts",
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return results[0] if results else None

    def enrich(self, alert: Alert) -> Alert:
        result = self._search_alerts()
        if not result:
            return alert

        obj = {"result": result}

        mapping = {
            "alert_id":    lambda r: alert.alert_id,
            "alert_type":  lambda r: r("result.security_domain") or alert.alert_type,
            "description": lambda r: (
                f"{r('result.rule_name')} — urgency: {r('result.urgency')}"
                if r("result.rule_name") else alert.description
            ),
            "severity":    lambda r: r("result.urgency") or alert.severity,
            "source":      lambda r: "Splunk",
            "hostname":    "result.host",
            "ip_addressV4": "result.src",
        }

        return translate(obj, mapping)
