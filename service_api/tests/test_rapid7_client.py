from unittest.mock import MagicMock, patch
import pytest
import httpx
from api.v1.models.alerts import Alert
from api.v1.services.rapid7_client import Rapid7Client


@pytest.fixture
def client():
    return Rapid7Client()


@pytest.fixture
def base_alert():
    return Alert(
        alert_id="test-uuid-1234",
        alert_type="unknown",
        description="Suspicious login",
        severity="high",
        source="Rapid7",
        hostname="WS-ACCT-0142",
    )


ASSET_RESPONSE = {
    "data": [
        {
            "rrn": "rrn:asset:us:abc:asset:xyz",
            "host_name": "WS-ACCT-0142",
            "ip_address": "10.42.18.55",
        }
    ]
}

ALERT_RESPONSE = {
    "data": [
        {
            "event_type": "process_start",
            "command_line": "powershell.exe -nop -w hidden",
            "remote_port": 80,
            "alert_id": "alert-abc-123",
        }
    ]
}


def mock_post(url, **kwargs):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    if "search_assets" in url:
        response.json.return_value = ASSET_RESPONSE
    elif "search_alerts" in url:
        response.json.return_value = ALERT_RESPONSE
    return response


class TestRapid7ClientEnrich:

    def test_returns_original_alert_when_hostname_is_none(self, client, base_alert):
        base_alert.hostname = None
        result = client.enrich(base_alert)
        assert result is base_alert

    def test_returns_original_alert_when_asset_not_found(self, client, base_alert):
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status = MagicMock()
            mock.return_value.json.return_value = {"data": []}
            result = client.enrich(base_alert)
        assert result is base_alert

    def test_returns_original_alert_when_alert_not_found(self, client, base_alert):
        def side_effect(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()
            if "search_assets" in url:
                response.json.return_value = ASSET_RESPONSE
            elif "search_alerts" in url:
                response.json.return_value = {"data": []}
            return response

        with patch("httpx.post", side_effect=side_effect):
            result = client.enrich(base_alert)
        assert result is base_alert

    def test_enrich_maps_fields_correctly(self, client, base_alert):
        with patch("httpx.post", side_effect=mock_post):
            result = client.enrich(base_alert)

        assert result.alert_id == "test-uuid-1234"
        assert result.alert_type == "process_start"
        assert result.hostname == "WS-ACCT-0142"
        assert result.ip_addressV4 == "10.42.18.55"
        assert result.port == 80
        assert result.source == "Rapid7"
        assert result.severity == "high"
        assert "process_start" in result.description
        assert "powershell.exe" in result.description

    def test_enrich_preserves_original_alert_id(self, client, base_alert):
        with patch("httpx.post", side_effect=mock_post):
            result = client.enrich(base_alert)
        assert result.alert_id == base_alert.alert_id

    def test_raises_on_http_error(self, client, base_alert):
        with patch("httpx.post") as mock:
            mock.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(httpx.HTTPStatusError):
                client.enrich(base_alert)
