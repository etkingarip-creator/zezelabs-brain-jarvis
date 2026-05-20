"""
Zezelabs Operator Runtime — Policy Engine
All tool execution decisions flow through here. Fail-closed by default.
"""
from __future__ import annotations
import os
import logging
from .contracts import PolicyDecision, RiskLevel, ApprovalStatus, ToolRequest

log = logging.getLogger("zom.policy")

# ── Allowlisted safe shell commands (read-only, non-destructive) ───────────────
SHELL_ALLOWLIST = frozenset([
    "ls", "dir", "pwd", "echo", "cat", "head", "tail", "grep", "find",
    "python --version", "node --version", "git status", "git log", "git diff",
    "git branch", "pip list", "npm list",
])

# ── File paths that are always protected regardless of department ──────────────
PROTECTED_PATHS = frozenset([
    ".env", ".env.local", ".env.production", ".env.secret",
    "id_rsa", "id_ed25519", "*.pem", "*.key", "*.p12",
    "wallet.json", "keystore", "mnemonic.txt",
])


class PolicyEngine:
    """
    Central policy enforcement. Every tool call must pass through here.
    Default stance: deny unless explicitly allowed.
    """

    def __init__(self, department: str = "general"):
        self.department = department
        self._live_trade_enabled = os.getenv("ZOM_ENABLE_LIVE_TRADING", "false").lower() == "true"
        self._withdrawal_enabled = False  # ALWAYS False — hardcoded

    # ── Shell ──────────────────────────────────────────────────────────────────
    def can_execute_shell(self, command: str) -> PolicyDecision:
        cmd_lower = command.strip().lower()
        # Blocklist: always deny destructive or injection patterns
        blocklist = ["rm -rf", "del /s", "format", "mkfs", "shutdown", "reboot",
                     "; rm", "&&rm", "| rm", "eval(", "exec(", "os.system"]
        for bad in blocklist:
            if bad in cmd_lower:
                log.warning(f"[POLICY] DENIED shell command (blocklist match '{bad}'): {command[:60]}")
                return PolicyDecision(allowed=False, reason=f"Blocklisted pattern: {bad}", risk_level=RiskLevel.CRITICAL)

        # Allowlist: safe read-only commands run without approval
        for safe in SHELL_ALLOWLIST:
            if cmd_lower.startswith(safe):
                return PolicyDecision(allowed=True, reason="Allowlisted command", risk_level=RiskLevel.LOW)

        # Everything else: requires approval
        log.info(f"[POLICY] Shell command requires approval: {command[:60]}")
        return PolicyDecision(
            allowed=False,
            approval_status=ApprovalStatus.PENDING,
            reason="Shell commands outside allowlist require human approval",
            risk_level=RiskLevel.HIGH,
        )

    # ── File Operations ────────────────────────────────────────────────────────
    def can_read_file(self, path: str) -> PolicyDecision:
        if self._is_protected_path(path):
            return PolicyDecision(allowed=False, reason=f"Protected path: {path}", risk_level=RiskLevel.CRITICAL)
        return PolicyDecision(allowed=True, reason="File read allowed", risk_level=RiskLevel.LOW)

    def can_edit_file(self, path: str, workspace_root: str) -> PolicyDecision:
        if self._is_protected_path(path):
            return PolicyDecision(allowed=False, reason=f"Protected path: {path}", risk_level=RiskLevel.CRITICAL)
        if not self._is_inside_workspace(path, workspace_root):
            return PolicyDecision(allowed=False, reason="File edit outside workspace denied", risk_level=RiskLevel.CRITICAL)
        return PolicyDecision(allowed=True, reason="File edit inside workspace allowed", risk_level=RiskLevel.LOW)

    # ── Git ────────────────────────────────────────────────────────────────────
    def can_push_git(self) -> PolicyDecision:
        return PolicyDecision(
            allowed=False,
            approval_status=ApprovalStatus.PENDING,
            reason="Git push requires human approval",
            risk_level=RiskLevel.HIGH,
        )

    def can_force_push_git(self) -> PolicyDecision:
        return PolicyDecision(allowed=False, reason="Force push is permanently denied", risk_level=RiskLevel.CRITICAL)

    # ── Deploy ─────────────────────────────────────────────────────────────────
    def can_deploy(self) -> PolicyDecision:
        return PolicyDecision(
            allowed=False,
            approval_status=ApprovalStatus.PENDING,
            reason="Deployment requires human approval",
            risk_level=RiskLevel.HIGH,
        )

    # ── Trading ────────────────────────────────────────────────────────────────
    def can_trade_paper(self) -> PolicyDecision:
        if self.department == "crypto_trading":
            return PolicyDecision(allowed=True, reason="Paper trading allowed for crypto department", risk_level=RiskLevel.LOW)
        return PolicyDecision(allowed=False, reason="Paper trading only allowed in crypto department", risk_level=RiskLevel.MEDIUM)

    def can_trade_live(self) -> PolicyDecision:
        if self._live_trade_enabled:
            return PolicyDecision(
                allowed=False,
                approval_status=ApprovalStatus.PENDING,
                reason="Live trading requires explicit human approval",
                risk_level=RiskLevel.CRITICAL,
            )
        return PolicyDecision(allowed=False, reason="Live trading is disabled (ZOM_ENABLE_LIVE_TRADING=false)", risk_level=RiskLevel.CRITICAL)

    def can_withdraw(self) -> PolicyDecision:
        return PolicyDecision(allowed=False, reason="Withdrawals are permanently denied", risk_level=RiskLevel.CRITICAL)

    # ── Approval Gate ──────────────────────────────────────────────────────────
    def requires_approval(self, request: ToolRequest) -> bool:
        high_risk_tools = {"shell_exec", "git_push", "deploy", "live_trade", "file_delete"}
        return request.tool_name in high_risk_tools or request.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    # ── Helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _is_protected_path(path: str) -> bool:
        lower = path.lower()
        protected_names = [".env", "id_rsa", "id_ed25519", ".pem", ".key",
                           ".p12", "wallet.json", "mnemonic", "keystore", "secret"]
        return any(p in lower for p in protected_names)

    @staticmethod
    def _is_inside_workspace(path: str, workspace_root: str) -> bool:
        import os.path
        abs_path = os.path.realpath(os.path.abspath(path))
        abs_root = os.path.realpath(os.path.abspath(workspace_root))
        return abs_path.startswith(abs_root)
