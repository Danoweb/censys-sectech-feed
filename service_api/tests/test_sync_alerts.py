from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
from api.v1.models.alerts import Alert
from api.v1.models.sync import Sync
from api.v1.services.sync_alerts import SyncAlerts


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return SyncAlerts(db)


def make_sync(minutes_ago: int, status: str = "success") -> Sync:
    s = Sync()
    s.sync__at = datetime.now(tz=timezone.utc) - timedelta(minutes=minutes_ago)
    s.sync_status = status
    return s


MOCK_ALERTS_RESPONSE = {
    "alerts": [
        {
            "alert_id": "uuid-aaa",
            "source": "Splunk",
            "severity": "high",
            "description": "Test alert",
            "created_at": "2026-03-14T12:00:00Z",
        },
        {
            "alert_id": "uuid-bbb",
            "source": "unknown-source",
            "severity": "low",
            "description": "Another alert",
            "created_at": "2026-03-14T12:01:00Z",
        },
    ]
}


class TestGetLastSuccessfulSync:

    def test_returns_most_recent_successful_sync(self, service, db):
        expected = make_sync(5)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = expected
        result = service.get_last_successful_sync()
        assert result is expected

    def test_returns_none_when_no_sync_exists(self, service, db):
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = service.get_last_successful_sync()
        assert result is None


class TestIsSyncDue:

    def test_returns_true_when_no_sync_record(self, service, db):
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        assert service.is_sync_due() is True

    def test_returns_true_when_interval_exceeded(self, service, db):
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = make_sync(120)
        with patch("api.v1.services.sync_alerts.settings") as mock_settings:
            mock_settings.SYNC_INTERVAL_MINUTES = 60
            assert service.is_sync_due() is True

    def test_returns_false_when_within_interval(self, service, db):
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = make_sync(5)
        with patch("api.v1.services.sync_alerts.settings") as mock_settings:
            mock_settings.SYNC_INTERVAL_MINUTES = 60
            assert service.is_sync_due() is False

    def test_handles_naive_datetime(self, service, db):
        sync = Sync()
        sync.sync__at = datetime.utcnow()  # naive, no tzinfo
        sync.sync_status = "success"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sync
        with patch("api.v1.services.sync_alerts.settings") as mock_settings:
            mock_settings.SYNC_INTERVAL_MINUTES = 60
            result = service.is_sync_due()
        assert isinstance(result, bool)


class TestRunSync:

    def test_skips_when_not_due(self, service, db):
        with patch.object(service, "is_sync_due", return_value=False):
            result = service.run_sync(use_safe_interval=True)
        assert result == {"synced": False, "reason": "within interval"}
        db.add.assert_not_called()

    def test_bypasses_interval_check_when_disabled(self, service, db):
        with patch.object(service, "is_sync_due", return_value=False), \
             patch.object(service, "get_alerts", return_value={"alerts": []}):
            result = service.run_sync(use_safe_interval=False)
        assert result["synced"] is True

    def test_saves_alerts_and_writes_sync_record(self, service, db):
        with patch.object(service, "is_sync_due", return_value=True), \
             patch.object(service, "get_alerts", return_value=MOCK_ALERTS_RESPONSE), \
             patch("api.v1.services.sync_alerts.SplunkClient") as mock_splunk:
            mock_splunk.return_value.enrich.side_effect = lambda a: a
            result = service.run_sync()

        assert result["synced"] is True
        assert result["count"] == 2
        assert db.commit.called

    def test_enrichment_failure_does_not_block_other_alerts(self, service, db):
        with patch.object(service, "is_sync_due", return_value=True), \
             patch.object(service, "get_alerts", return_value=MOCK_ALERTS_RESPONSE), \
             patch("api.v1.services.sync_alerts.SplunkClient") as mock_splunk:
            mock_splunk.return_value.enrich.side_effect = Exception("enrichment boom")
            result = service.run_sync()

        assert result["synced"] is True
        assert db.commit.called

    def test_save_failure_for_one_alert_does_not_block_others(self, service, db):
        flush_calls = [0]

        def flush_side_effect():
            flush_calls[0] += 1
            if flush_calls[0] == 1:
                raise Exception("unique constraint")

        db.flush.side_effect = flush_side_effect

        with patch.object(service, "is_sync_due", return_value=True), \
             patch.object(service, "get_alerts", return_value=MOCK_ALERTS_RESPONSE):
            result = service.run_sync()

        assert result["synced"] is True
        assert result["count"] == 1
        assert db.commit.called


class TestGetAlerts:

    def test_uses_last_sync_time_as_since(self, service, db):
        last_sync = make_sync(30)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_sync

        mock_response = MagicMock()
        mock_response.json.return_value = {"alerts": []}

        with patch("httpx.get", return_value=mock_response) as mock_get, \
             patch("api.v1.services.sync_alerts.settings") as mock_settings:
            mock_settings.ALERTS_API_URL = "http://alerts_api:8000"
            service.get_alerts()

        call_params = mock_get.call_args[1]["params"]
        assert "since" in call_params

    def test_falls_back_to_epoch_when_no_sync(self, service, db):
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"alerts": []}

        with patch("httpx.get", return_value=mock_response) as mock_get, \
             patch("api.v1.services.sync_alerts.settings") as mock_settings:
            mock_settings.ALERTS_API_URL = "http://alerts_api:8000"
            service.get_alerts()

        call_params = mock_get.call_args[1]["params"]
        assert "1970" in call_params["since"]

    def test_raises_on_http_error(self, service, db):
        import httpx
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with patch("httpx.get") as mock_get, \
             patch("api.v1.services.sync_alerts.settings") as mock_settings:
            mock_settings.ALERTS_API_URL = "http://alerts_api:8000"
            mock_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(httpx.HTTPStatusError):
                service.get_alerts()
