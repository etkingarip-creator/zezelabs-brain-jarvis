"""
Zezelabs Operator Runtime — Contracts
Canonical data structures for all tool requests, policy decisions, and results.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING      = "pending"
    APPROVED     = "approved"
    DENIED       = "denied"


class DepartmentName(str, Enum):
    APP_FACTORY    = "app_factory"
    CRYPTO_TRADING = "crypto_trading"
    MEDIA          = "media"
    SALES          = "sales"
    MARKETING      = "marketing"
    FINANCE        = "finance"
    STRATEGY       = "strategy"
    DEVOPS         = "devops"
    SECURITY       = "security"
    GENERAL        = "general"


# ── Core Contracts ─────────────────────────────────────────────────────────────

@dataclass
class TaskEnvelope:
    """Top-level task submitted by Brain/Planner to the Orchestrator."""
    user_goal: str
    department: str
    task_id: str                    = field(default_factory=lambda: str(uuid.uuid4()))
    risk_level: RiskLevel           = RiskLevel.LOW
    approval_required: bool         = False
    metadata: Dict[str, Any]        = field(default_factory=dict)
    created_at: datetime            = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ToolRequest:
    """A single tool invocation request from a Department Agent."""
    tool_name: str
    action: str
    task_id: str                    = field(default_factory=lambda: str(uuid.uuid4()))
    department: str                 = DepartmentName.GENERAL
    args: Dict[str, Any]            = field(default_factory=dict)
    cwd: Optional[str]              = None
    risk_level: RiskLevel           = RiskLevel.LOW


@dataclass
class ToolResult:
    """Result of a tool execution."""
    task_id: str
    tool_name: str
    success: bool
    stdout: str                     = ""
    stderr: str                     = ""
    error: Optional[str]            = None
    started_at: Optional[datetime]  = None
    finished_at: Optional[datetime] = None


@dataclass
class PolicyDecision:
    """Decision returned by PolicyEngine for a given ToolRequest."""
    allowed: bool
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    reason: str                     = ""
    risk_level: RiskLevel           = RiskLevel.LOW


@dataclass
class AgentResult:
    """Final result returned to the Orchestrator from a Department Agent."""
    task_id: str
    department: str
    success: bool
    output: str                     = ""
    tool_results: list              = field(default_factory=list)
    error: Optional[str]            = None
    finished_at: datetime           = field(default_factory=lambda: datetime.now(timezone.utc))
