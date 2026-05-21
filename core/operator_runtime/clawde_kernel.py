"""
Zezelabs Operator Runtime — Clawde Operator Kernel
Single official bridge between ZOM departments and Clawde_Code tool runtime.
Every call: PolicyCheck -> (ApprovalGate) -> Execute -> Telemetry.
"""
from __future__ import annotations
import logging
import os
import shlex
import subprocess
from datetime import datetime, timezone

from .contracts import ToolRequest, ToolResult, RiskLevel, ApprovalStatus
from .policy_engine import PolicyEngine
from .telemetry import get_telemetry
from .workspace_guard import WorkspaceGuard
from core.mcp_client import MCPClient

log = logging.getLogger("zom.clawde_kernel")

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKSPACE_ROOT = os.getenv("WORKSPACE_DIR", os.path.join(project_root, "workspace"))


class ClawdeOperatorKernel:
    """
    Policy-gated operator kernel. Wraps Clawde_Code tool capabilities.
    Fail-closed: any policy denial returns ToolResult(success=False).
    """

    def __init__(self, department: str = "general", workspace_root: str = WORKSPACE_ROOT):
        self.department = department
        self.policy = PolicyEngine(department=department)
        self.guard = WorkspaceGuard(workspace_root)
        self.telemetry = get_telemetry()

    # ── Windows-safe command normalizer ────────────────────────────────────────
    def _normalize_shell_command(self, command: str) -> list:
        parts = shlex.split(command, posix=(os.name != "nt"))
        if not parts:
            return []
        # On Windows: map POSIX 'ls' to 'dir' via cmd
        if os.name == "nt" and parts[0].lower() in {"ls"}:
            return ["cmd", "/c", "dir"]
        return parts

    # ── Shell Execution ────────────────────────────────────────────────────────
    def execute_shell(self, request: ToolRequest) -> ToolResult:
        command = request.args.get("command", "")
        decision = self.policy.can_execute_shell(command)
        started = datetime.now(timezone.utc)

        if not decision.allowed:
            status = "approval_pending" if decision.approval_status == ApprovalStatus.PENDING else "denied"
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="shell_exec", action=command[:80],
                status=status, risk_level=decision.risk_level.value,
                approval_required=(decision.approval_status == ApprovalStatus.PENDING),
                started_at=started, error=decision.reason,
            )
            return ToolResult(task_id=request.task_id, tool_name="shell_exec",
                              success=False, error=decision.reason,
                              started_at=started, finished_at=datetime.now(timezone.utc))

        cmd = self._normalize_shell_command(command)
        try:
            result = subprocess.run(
                cmd, shell=False,
                capture_output=True, text=True, timeout=30,
                cwd=request.cwd or WORKSPACE_ROOT,
            )
            success = result.returncode == 0
            finished = datetime.now(timezone.utc)
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="shell_exec", action=command[:80],
                status="success" if success else "error",
                risk_level=decision.risk_level.value,
                started_at=started, finished_at=finished,
                error=result.stderr if not success else None,
            )
            return ToolResult(task_id=request.task_id, tool_name="shell_exec",
                              success=success, stdout=result.stdout, stderr=result.stderr,
                              started_at=started, finished_at=finished)
        except Exception as e:
            finished = datetime.now(timezone.utc)
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="shell_exec", action=command[:80],
                status="error", risk_level=RiskLevel.HIGH.value,
                started_at=started, finished_at=finished, error=str(e),
            )
            return ToolResult(task_id=request.task_id, tool_name="shell_exec",
                              success=False, error=str(e),
                              started_at=started, finished_at=finished)

    # ── File Read ──────────────────────────────────────────────────────────────
    def read_file(self, request: ToolRequest) -> ToolResult:
        path = request.args.get("path", "")
        allowed, reason = self.guard.check_read(path)
        started = datetime.now(timezone.utc)

        if not allowed:
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="file_read", action=path,
                status="denied", risk_level=RiskLevel.CRITICAL.value,
                started_at=started, error=reason,
            )
            return ToolResult(task_id=request.task_id, tool_name="file_read",
                              success=False, error=reason, started_at=started,
                              finished_at=datetime.now(timezone.utc))

        try:
            content = open(path, "r", encoding="utf-8", errors="replace").read()
            finished = datetime.now(timezone.utc)
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="file_read", action=path,
                status="success", risk_level=RiskLevel.LOW.value,
                started_at=started, finished_at=finished,
            )
            return ToolResult(task_id=request.task_id, tool_name="file_read",
                              success=True, stdout=content,
                              started_at=started, finished_at=finished)
        except Exception as e:
            return ToolResult(task_id=request.task_id, tool_name="file_read",
                              success=False, error=str(e),
                              started_at=started, finished_at=datetime.now(timezone.utc))

    # ── File Edit ──────────────────────────────────────────────────────────────
    def edit_file(self, request: ToolRequest) -> ToolResult:
        path = request.args.get("path", "")
        content = request.args.get("content", "")
        allowed, reason = self.guard.check_write(path)
        started = datetime.now(timezone.utc)

        if not allowed:
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="file_edit", action=path,
                status="denied", risk_level=RiskLevel.CRITICAL.value,
                started_at=started, error=reason,
            )
            return ToolResult(task_id=request.task_id, tool_name="file_edit",
                              success=False, error=reason, started_at=started,
                              finished_at=datetime.now(timezone.utc))

        try:
            import pathlib
            pathlib.Path(path).write_text(content, encoding="utf-8")
            finished = datetime.now(timezone.utc)
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="file_edit", action=path,
                status="success", risk_level=RiskLevel.LOW.value,
                started_at=started, finished_at=finished,
            )
            return ToolResult(task_id=request.task_id, tool_name="file_edit",
                              success=True, stdout=f"Written: {path}",
                              started_at=started, finished_at=finished)
        except Exception as e:
            return ToolResult(task_id=request.task_id, tool_name="file_edit",
                              success=False, error=str(e),
                              started_at=started, finished_at=datetime.now(timezone.utc))

    # ── Git Operations ─────────────────────────────────────────────────────────
    def git_operation(self, request: ToolRequest) -> ToolResult:
        action = request.args.get("action", "")
        started = datetime.now(timezone.utc)

        if "push" in action.lower():
            if "--force" in action:
                decision = self.policy.can_force_push_git()
            else:
                decision = self.policy.can_push_git()
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name="git_operation", action=action,
                status="approval_pending", risk_level=RiskLevel.HIGH.value,
                approval_required=True, started_at=started, error=decision.reason,
            )
            return ToolResult(task_id=request.task_id, tool_name="git_operation",
                              success=False, error=decision.reason,
                              started_at=started, finished_at=datetime.now(timezone.utc))

        # Safe read-only git ops allowed
        safe_git = ["status", "log", "diff", "branch", "show"]
        if any(s in action.lower() for s in safe_git):
            cmd = f"git {action}"
            req = ToolRequest(tool_name="shell_exec", action=action,
                              task_id=request.task_id, department=self.department,
                              args={"command": cmd}, cwd=request.cwd)
            return self.execute_shell(req)

        return ToolResult(task_id=request.task_id, tool_name="git_operation",
                          success=False, error=f"Git action '{action}' requires approval",
                          started_at=started, finished_at=datetime.now(timezone.utc))

    # ── Browser Action ─────────────────────────────────────────────────────────
    def browser_action(self, request: ToolRequest) -> ToolResult:
        started = datetime.now(timezone.utc)
        # Browser automation is routed through Clawde_Code WebFetchTool / playwright
        # For now: stub returning not-yet-implemented (safe default)
        self.telemetry.record_execution(
            task_id=request.task_id, department=self.department,
            tool_name="browser_action", action=request.action,
            status="not_implemented", risk_level=RiskLevel.MEDIUM.value,
            started_at=started,
        )
        return ToolResult(task_id=request.task_id, tool_name="browser_action",
                          success=False, error="Browser automation not yet connected to Clawde runtime",
                          started_at=started, finished_at=datetime.now(timezone.utc))

    # ── MCP Tool Execution ──────────────────────────────────────────────────────
    async def execute_mcp_tool(self, request: ToolRequest, client: MCPClient) -> ToolResult:
        started = datetime.now(timezone.utc)
        tool_name = request.tool_name
        args = request.args or {}
        
        # 1. Registry allowed/forbidden lists check
        from core.registry import DEPARTMENTS
        dept_config = DEPARTMENTS.get(self.department, {})
        allowed_tools = dept_config.get("allowed_tools", [])
        forbidden_tools = dept_config.get("forbidden_tools", [])
        
        if tool_name in forbidden_tools:
            reason = f"Security Violation: Tool '{tool_name}' is forbidden for department '{self.department}'."
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name=tool_name, action=request.action,
                status="denied", risk_level=RiskLevel.CRITICAL.value,
                started_at=started, error=reason,
            )
            return ToolResult(task_id=request.task_id, tool_name=tool_name,
                              success=False, error=reason,
                              started_at=started, finished_at=datetime.now(timezone.utc))
                              
        if allowed_tools and tool_name not in allowed_tools:
            reason = f"Security Violation: Tool '{tool_name}' is not in the allowlist for department '{self.department}'."
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name=tool_name, action=request.action,
                status="denied", risk_level=RiskLevel.CRITICAL.value,
                started_at=started, error=reason,
            )
            return ToolResult(task_id=request.task_id, tool_name=tool_name,
                              success=False, error=reason,
                              started_at=started, finished_at=datetime.now(timezone.utc))
        
        # 2. Input Sanitization (Path traversal and dangerous payload check)
        for key, val in args.items():
            val_str = str(val)
            # Path traversal check
            if ".." in val_str:
                reason = f"Security Violation: Path traversal detected in argument '{key}'."
                self.telemetry.record_execution(
                    task_id=request.task_id, department=self.department,
                    tool_name=tool_name, action=request.action,
                    status="denied", risk_level=RiskLevel.CRITICAL.value,
                    started_at=started, error=reason,
                )
                return ToolResult(task_id=request.task_id, tool_name=tool_name,
                                  success=False, error=reason,
                                  started_at=started, finished_at=datetime.now(timezone.utc))
            
            # Sensitive path name check
            lower_val = val_str.lower()
            sensitive = [".env", "wallet.json", "id_rsa", "mnemonic", "keystore", "secret"]
            if any(s in lower_val for s in sensitive):
                reason = f"Security Violation: Access to protected file pattern in argument '{key}'."
                self.telemetry.record_execution(
                    task_id=request.task_id, department=self.department,
                    tool_name=tool_name, action=request.action,
                    status="denied", risk_level=RiskLevel.CRITICAL.value,
                    started_at=started, error=reason,
                )
                return ToolResult(task_id=request.task_id, tool_name=tool_name,
                                  success=False, error=reason,
                                  started_at=started, finished_at=datetime.now(timezone.utc))
            
            # Dangerous shell inject block
            dangerous_patterns = ["rm -rf", "del /s", "format ", "mkfs", "eval(", "exec(", "os.system"]
            if any(d in lower_val for d in dangerous_patterns):
                reason = f"Security Violation: Blocklisted command pattern detected in argument '{key}'."
                self.telemetry.record_execution(
                    task_id=request.task_id, department=self.department,
                    tool_name=tool_name, action=request.action,
                    status="denied", risk_level=RiskLevel.CRITICAL.value,
                    started_at=started, error=reason,
                )
                return ToolResult(task_id=request.task_id, tool_name=tool_name,
                                  success=False, error=reason,
                                  started_at=started, finished_at=datetime.now(timezone.utc))
        
        # 3. Call the MCP client
        try:
            resp = await client.call_tool(tool_name, args)
            finished = datetime.now(timezone.utc)
            if not resp or "error" in resp:
                err_msg = resp.get("error", {}).get("message", "Unknown error") if resp else "Empty response"
                self.telemetry.record_execution(
                    task_id=request.task_id, department=self.department,
                    tool_name=tool_name, action=request.action,
                    status="error", risk_level=RiskLevel.LOW.value,
                    started_at=started, finished_at=finished, error=err_msg,
                )
                return ToolResult(task_id=request.task_id, tool_name=tool_name,
                                  success=False, error=err_msg,
                                  started_at=started, finished_at=finished)
            
            result_data = resp.get("result", "")
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name=tool_name, action=request.action,
                status="success", risk_level=RiskLevel.LOW.value,
                started_at=started, finished_at=finished,
            )
            return ToolResult(task_id=request.task_id, tool_name=tool_name,
                              success=True, stdout=str(result_data),
                              started_at=started, finished_at=finished)
        except Exception as e:
            finished = datetime.now(timezone.utc)
            self.telemetry.record_execution(
                task_id=request.task_id, department=self.department,
                tool_name=tool_name, action=request.action,
                status="error", risk_level=RiskLevel.HIGH.value,
                started_at=started, finished_at=finished, error=str(e),
            )
            return ToolResult(task_id=request.task_id, tool_name=tool_name,
                              success=False, error=str(e),
                              started_at=started, finished_at=finished)
