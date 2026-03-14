from unittest.mock import MagicMock, patch
import pytest
import httpx
from api.v1.models.alerts import Alert
from api.v1.services.splunk_client import SplunkClient


@pytest.fixture
def client():
    return SplunkClient()


@pytest.fixture
def base_alert():
    return Alert(
        alert_id="test-uuid-9999",
        alert_type="unknown",
        description="Suspicious login",
        severity="medium",
        source="Splunk",
        hostname=None,
    )


SEARCH_RESPONSE = {
    "results": [
        {
            "orig_sid": "scheduler_admin_RMD5f3c2f8d_at_1710438120",
            "security_domain": "endpoint",
            "rule_name": "Suspicious PowerShell Download Cradle",
            "urgency": "high",
            "host": "WS-ACCT-0142",
            "src": "10.42.18.55",
        }
    ]
}


class TestSplunkClientEnrich:

    def test_returns_original_alert_when_no_results(self, client, base_alert):
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status = MagicMock()
            mock.return_value.json.return_value = {"results": []}
            result = client.enrich(base_alert)
        assert result is base_alert

    def test_enrich_maps_fields_correctly(self, client, base_alert):
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status = MagicMock()
            mock.return_value.json.return_value = SEARCH_RESPONSE

            result = client.enrich(base_alert)

        assert result.alert_id == "test-uuid-9999"
        assert result.alert_type == "endpoint"
        assert result.severity == "high"
        assert result.source == "Splunk"
        assert result.hostname == "WS-ACCT-0142"
        assert result.ip_addressV4 == "10.42.18.55"
        assert "Suspicious PowerShell Download Cradle" in result.description
        assert "urgency: high" in result.description

    def test_enrich_preserves_original_alert_id(self, client, base_alert):
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status = MagicMock()
            mock.return_value.json.return_value = SEARCH_RESPONSE
            result = client.enrich(base_alert)
        assert result.alert_id == base_alert.alert_id

    def test_falls_back_to_original_severity_when_urgency_missing(self, client, base_alert):
        response = {"results": [{"rule_name": "Test", "host": "host1", "src": "1.2.3.4"}]}
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status = MagicMock()
            mock.return_value.json.return_value = response
            result = client.enrich(base_alert)
        assert result.severity == base_alert.severity

    def test_raises_on_http_error(self, client, base_alert):
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(httpx.HTTPStatusError):
                client.enrich(base_alert)
