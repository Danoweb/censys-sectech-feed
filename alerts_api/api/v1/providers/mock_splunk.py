from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/splunk", tags=["splunk"])

"""
This is a mock implementation of the Splunk API endpoints for demonstration purposes.
The Splunk query used for this would be:
`notable`
| search host="WS-ACCT-0142"
| table _time rule_name urgency owner status security_domain orig_sid src dest user
"""
@router.post("/search_alerts")
def search_alerts():
    return {
      "preview": False,
      "init_offset": 0,
      "messages": [],
      "fields": [
        "_time",
        "host",
        "rule_name",
        "urgency",
        "owner",
        "status",
        "security_domain",
        "orig_sid",
        "src",
        "dest",
        "user"
      ],
      "results": [
        {
          "_time": "2026-03-14T13:42:05.000+00:00",
          "host": "WS-ACCT-0142",
          "rule_name": "Suspicious PowerShell Download Cradle",
          "urgency": "high",
          "owner": "unassigned",
          "status": "new",
          "security_domain": "endpoint",
          "orig_sid": "scheduler_admin_search_RMD5f3c2f8d_at_1710438120_4820",
          "src": "10.42.18.55",
          "dest": "198.51.100.25",
          "user": "CORP\\jdoe"
        }
      ]
    }
