from unittest.mock import MagicMock, patch
import pytest
import httpx
from api.v1.models.alerts import Alert
from api.v1.services.tanium_client import TaniumClient


@pytest.fixture
def client():
    return TaniumClient()


@pytest.fixture
def base_alert():
    return Alert(
        alert_id="test-uuid-5678",
        alert_type="unknown",
        description="Suspicious login",
        severity="critical",
        source="Tanium",
        hostname="WS-ACCT-0142",
    )


ENDPOINT_RESPONSE = {
    "data": {
        "endpoints": {
            "edges": [
                {
                    "node": {
                        "name": "WS-ACCT-0142",
                        "ipAddress": "10.42.18.55",
                    }
                }
            ]
        }
    }
}

ALERT_RESPONSE = {
    "data": {
        "alerts": [
            {
                "Alert Id": "87421",
                "Intel Name": "Suspicious PowerShell Download Cradle",
                "Intel Type": "signal",
                "Intel Labels": "Execution, PowerShell, Suspicious",
                "MatchDetails": {
                    "match": {
                        "properties": {
                            "remote_port": 80,
                        }
                    }
                },
            }
        ]
    }
}


def mock_get(url, **kwargs):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    if "tanium_threat_response" in url:
        response.json.return_value = ENDPOINT_RESPONSE
    elif "get_alerts" in url:
        response.json.return_value = ALERT_RESPONSE
    return response


class TestTaniumClientEnrich:

    def test_returns_original_alert_when_no_endpoint_found(self, client, base_alert):
        with patch("httpx.get") as mock:
            mock.return_value.raise_for_status = MagicMock()
            mock.return_value.json.return_value = {
                "data": {"endpoints": {"edges": []}}
            }
            result = client.enrich(base_alert)
        assert result is base_alert

    def test_returns_original_alert_when_no_tanium_alert_found(self, client, base_alert):
        def side_effect(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()
            if "tanium_threat_response" in url:
                response.json.return_value = ENDPOINT_RESPONSE
            elif "get_alerts" in url:
                response.json.return_value = {"data": {"alerts": []}}
            return response

        with patch("httpx.get", side_effect=side_effect):
            result = client.enrich(base_alert)
        assert result is base_alert

    def test_enrich_maps_fields_correctly(self, client, base_alert):
        with patch("httpx.get", side_effect=mock_get):
            result = client.enrich(base_alert)

        assert result.alert_id == "test-uuid-5678"
        assert result.alert_type == "signal"
        assert result.hostname == "WS-ACCT-0142"
        assert result.ip_addressV4 == "10.42.18.55"
        assert result.port == 80
        assert result.source == "Tanium"
        assert "Suspicious PowerShell Download Cradle" in result.description
        assert "Execution, PowerShell, Suspicious" in result.description

    def test_enrich_preserves_original_alert_id(self, client, base_alert):
        with patch("httpx.get", side_effect=mock_get):
            result = client.enrich(base_alert)
        assert result.alert_id == base_alert.alert_id

    def test_hostname_none_falls_back_to_first_edge(self, client, base_alert):
        base_alert.hostname = None
        with patch("httpx.get", side_effect=mock_get):
            result = client.enrich(base_alert)
        assert result.hostname == "WS-ACCT-0142"

    def test_raises_on_http_error(self, client, base_alert):
        with patch("httpx.get") as mock:
            mock.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(httpx.HTTPStatusError):
                client.enrich(base_alert)
