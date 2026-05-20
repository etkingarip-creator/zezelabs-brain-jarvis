from typing import Dict, Any, Optional

class Storage:
    """Simple in-memory storage for ZezeGuard MVP"""
    def __init__(self):
        self.events = []
        self.costs = []
        self.outcomes = []
        self.alerts = []

    def clear(self):
        self.events.clear()
        self.costs.clear()
        self.outcomes.clear()
        self.alerts.clear()

storage_instance = Storage()

def get_storage() -> Storage:
    return storage_instance
