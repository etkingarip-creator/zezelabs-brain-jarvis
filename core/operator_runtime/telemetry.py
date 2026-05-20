"""
Zezelabs Operator Runtime — Telemetry
Every tool execution event is logged here. Immutable audit trail.
"""
from __future__ import annotations
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

log = logging.getLogger("zom.telemetry")


@dataclass
class TelemetryEvent:
    event_id: str               = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str                = ""
    department: str             = ""
    tool_name: str              = ""
    action: str                 = ""
    status: str                 = ""        # "success" | "denied" | "error" | "approval_pending"
    risk_level: str             = "low"
    approval_required: bool     = False
    started_at: Optional[str]   = None
    finished_at: Optional[str]  = None
    error: Optional[str]        = None

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "department": self.department,
            "tool_name": self.tool_name,
            "action": self.action,
            "status": self.status,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }
class Telemetry:
    """In-memory telemetry store with structured logging. Swap for Redis/DB in prod."""

    def __init__(self):
        self._events: List[TelemetryEvent] = []

    def record(self, event: TelemetryEvent) -> None:
        self._events.append(event)
        log.info(f"[TELEMETRY] {event.status.upper()} | dept={event.department} "
                 f"tool={event.tool_name} action={event.action} "
                 f"risk={event.risk_level} task={event.task_id[:8]}")

    def record_execution(
        self,
        task_id: str,
        department: str,
        tool_name: str,
        action: str,
        status: str,
        risk_level: str = "low",
        approval_required: bool = False,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            task_id=task_id,
            department=department,
            tool_name=tool_name,
            action=action,
            status=status,
            risk_level=risk_level,
            approval_required=approval_required,
            started_at=started_at.isoformat() if started_at else None,
            finished_at=finished_at.isoformat() if finished_at else datetime.now(timezone.utc).isoformat(),
            error=error,
        )
        self.record(event)
        return event

    def get_events(self) -> List[TelemetryEvent]:
        return list(self._events)

    def get_events_for_task(self, task_id: str) -> List[TelemetryEvent]:
        return [e for e in self._events if e.task_id == task_id]

    def to_json(self) -> str:
        return json.dumps([asdict(e) for e in self._events], indent=2)


# Singleton for runtime use
_telemetry = Telemetry()

def get_telemetry() -> Telemetry:
    return _telemetry
