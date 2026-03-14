import random
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["alerts"])

def get_severity_level() -> str:
    severity_mapping = ["low", "medium", "high", "critical"]
    return random.choice(severity_mapping)

def get_source() -> str:
    source_mapping = [
        "Splunk",
        "Elasticsearch Endgame",
        "Tanium",
        "Rapid7",
        "CrowdStrike",
        "Carbon Black",
        "SentinelOne",
        "Exabeam",
        "Google Chronicle",
        "AWS CloudTrail",
    ]
    return random.choice(source_mapping)

@router.get("/alerts")
def get_alerts(
    since: datetime = Query(..., description="ISO8601 timestamp to filter alerts from"),
):
    # This simulates an issue on the upstream service, as required.
    if random.random() < 0.10:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    now = datetime.now(tz=timezone.utc)
    all_sources = [
        "Splunk", "Elasticsearch Endgame", "Tanium", "Rapid7",
        "CrowdStrike", "Carbon Black", "SentinelOne", "Exabeam",
        "Google Chronicle", "AWS CloudTrail",
    ]
    sources = random.sample(all_sources, 5)
    severities = random.choices(["low", "medium", "high", "critical"], k=5)

    return {
        "alerts": [
            {
                "alert_id": str(uuid.uuid4()),
                "source": sources[i],
                "severity": severities[i],
                "description": "Suspicious login",
                "created_at": (now - timedelta(minutes=i)).isoformat(),
            }
            for i in range(5)
        ]
    }
