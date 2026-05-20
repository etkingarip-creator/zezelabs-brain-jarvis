"""
tests/test_clawde_kernel_mock.py
ClawdeOperatorKernel — policy gate and telemetry tests (no real execution)
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
from core.operator_runtime.contracts import ToolRequest, RiskLevel


WORKSPACE = os.path.abspath(".")


def kernel(dept="app_factory"):
    return ClawdeOperatorKernel(department=dept, workspace_root=WORKSPACE)


class TestClawdeKernelPolicy:
    def test_shell_allowlisted_command_allowed(self):
        k = kernel()
        # "git status" is allowlisted and works on all platforms
        req = ToolRequest(tool_name="shell_exec", action="git status", args={"command": "git status"})
        result = k.execute_shell(req)
        # Policy passes — error may come from git not being in a repo, but NOT from policy denial
        assert "Protected" not in (result.error or "")
        assert "denied" not in (result.error or "").lower()

    def test_shell_rm_rf_denied_by_policy(self):
        k = kernel()
        req = ToolRequest(tool_name="shell_exec", action="rm", args={"command": "rm -rf /"})
        result = k.execute_shell(req)
        assert result.success is False
        assert result.error is not None

    def test_shell_eval_denied_by_policy(self):
        k = kernel()
        req = ToolRequest(tool_name="shell_exec", action="eval", args={"command": "eval(x)"})
        result = k.execute_shell(req)
        assert result.success is False

    def test_file_read_protected_path_denied(self):
        k = kernel()
        req = ToolRequest(tool_name="file_read", action="read", args={"path": ".env"})
        result = k.read_file(req)
        assert result.success is False
        assert "Protected" in result.error

    def test_file_edit_outside_workspace_denied(self):
        k = kernel()
        req = ToolRequest(tool_name="file_edit", action="write",
                          args={"path": "/etc/hosts", "content": "bad"})
        result = k.edit_file(req)
        assert result.success is False

    def test_git_push_denied(self):
        k = kernel()
        req = ToolRequest(tool_name="git_operation", action="push",
                          args={"action": "push origin main"})
        result = k.git_operation(req)
        assert result.success is False
        assert "approval" in result.error.lower()

    def test_git_force_push_denied(self):
        k = kernel()
        req = ToolRequest(tool_name="git_operation", action="force_push",
                          args={"action": "push --force origin main"})
        result = k.git_operation(req)
        assert result.success is False

    def test_telemetry_records_event(self):
        from core.operator_runtime.telemetry import get_telemetry
        tel = get_telemetry()
        before = len(tel.get_events())
        k = kernel()
        req = ToolRequest(tool_name="shell_exec", action="rm", args={"command": "rm -rf /"})
        k.execute_shell(req)
        after = len(tel.get_events())
        assert after > before

    def test_kernel_requires_policy_before_execution(self):
        """Kernel must have a policy engine — cannot be None."""
        k = kernel()
        assert k.policy is not None
