from typing import Dict, Any, Optional
from core.zeze_guard.storage import get_storage
import logging

log = logging.getLogger("zeze_guard.shadow_ceo")

class ShadowCEOAlertClient:
    def __init__(self):
        self.storage = get_storage()

    def send_alert(self, title: str, message: str, severity: str = "warning", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        alert = {
            "title": title,
            "message": message,
            "severity": severity,
            "metadata": metadata or {}
        }
        self.storage.alerts.append(alert)
        log.warning(f"[SHADOW CEO] [{severity.upper()}] {title}: {message}")
        
        return {
            "sent": True,
            "channel": "mock_telegram",
            "severity": severity
        }
