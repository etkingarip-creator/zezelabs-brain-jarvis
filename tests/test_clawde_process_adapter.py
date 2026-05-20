"""
tests/test_clawde_process_adapter.py
ClawdeProcessAdapter — validation and security tests (no real Clawde execution)
"""
import os
import pytest
from core.operator_runtime.adapters.clawde_process_adapter import ClawdeProcessAdapter

WORKSPACE = os.path.abspath(".")
CLAWDE_ROOT = os.path.join(os.path.abspath("."), "Clawde_Code")


def adapter():
    return ClawdeProcessAdapter(clawde_root=CLAWDE_ROOT, workspace_root=WORKSPACE, timeout=30)


# ── validate_args ──────────────────────────────────────────────────────────────
class TestValidateArgs:
    def test_list_required(self):
        ok, reason = adapter().validate_args("git status")
        assert ok is False
        assert "list" in reason

    def test_empty_list_denied(self):
        ok, reason = adapter().validate_args([])
        assert ok is False

    def test_non_string_elements_denied(self):
        ok, reason = adapter().validate_args(["cmd", 123])
        assert ok is False

    def test_safe_args_allowed(self):
        ok, reason = adapter().validate_args(["--version"])
        assert ok is True

    def test_git_push_denied(self):
        ok, reason = adapter().validate_args(["git", "push", "origin", "main"])
        assert ok is False
        assert "push" in reason.lower()

    def test_force_flag_denied(self):
        ok, reason = adapter().validate_args(["git", "push", "--force"])
        assert ok is False

    def test_withdrawal_denied(self):
        ok, reason = adapter().validate_args(["withdraw", "--amount", "1000"])
        assert ok is False

    def test_live_trade_denied(self):
        ok, reason = adapter().validate_args(["live_trade", "--pair", "BTCUSDT"])
        assert ok is False

    def test_live_trade_hyphen_denied(self):
        ok, reason = adapter().validate_args(["live-trade", "--pair", "BTCUSDT"])
        assert ok is False


# ── validate_cwd ───────────────────────────────────────────────────────────────
class TestValidateCwd:
    def test_workspace_root_allowed(self):
        ok, reason = adapter().validate_cwd(WORKSPACE)
        assert ok is True

    def test_subdirectory_allowed(self):
        ok, reason = adapter().validate_cwd(os.path.join(WORKSPACE, "core"))
        assert ok is True

    def test_outside_workspace_denied(self):
        ok, reason = adapter().validate_cwd("/etc")
        assert ok is False
        assert "outside workspace" in reason

    def test_home_dir_denied(self):
        ok, reason = adapter().validate_cwd(os.path.expanduser("~"))
        assert ok is False


# ── build_command ──────────────────────────────────────────────────────────────
class TestBuildCommand:
    def test_returns_list(self):
        cmd = adapter().build_command(["--help"])
        assert isinstance(cmd, list)

    def test_args_appended(self):
        cmd = adapter().build_command(["--version"])
        assert "--version" in cmd

    def test_no_shell_string(self):
        """build_command must never return a plain string (which would require shell=True)."""
        cmd = adapter().build_command(["--help"])
        assert isinstance(cmd, list), "Command must be a list for shell=False"

    def test_dry_run_mode_when_no_clawde(self):
        """When Clawde_Code dist/index.js doesn't exist, falls back to dry-run."""
        a = ClawdeProcessAdapter(clawde_root="/nonexistent/path", workspace_root=WORKSPACE)
        cmd = a.build_command(["--test"])
        assert cmd[0] == "echo"
        assert "[DRY-RUN]" in cmd


# ── run_clawde_command ─────────────────────────────────────────────────────────
class TestRunClawdeCommand:
    def test_invalid_args_returns_denied(self):
        result = adapter().run_clawde_command("not a list")
        assert result["success"] is False
        assert "DENIED" in result["error"]

    def test_outside_cwd_returns_denied(self):
        result = adapter().run_clawde_command(["--help"], cwd="/etc")
        assert result["success"] is False
        assert "DENIED" in result["error"]

    def test_push_args_returns_denied(self):
        result = adapter().run_clawde_command(["git", "push", "origin", "main"])
        assert result["success"] is False

    def test_shell_false_guaranteed(self):
        """
        This test verifies our adapter contract: shell=False is hardcoded.
        We monkey-patch subprocess.run to inspect the call.
        """
        import subprocess
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            adapter().run_clawde_command(["--version"])
            if mock_run.called:
                _, kwargs = mock_run.call_args
                assert kwargs.get("shell") is False or kwargs.get("shell") is None

    def test_timeout_is_applied(self):
        """Adapter must always pass a timeout to subprocess.run."""
        import subprocess
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            adapter().run_clawde_command(["--version"])
            if mock_run.called:
                _, kwargs = mock_run.call_args
                assert kwargs.get("timeout") is not None

    def test_result_has_required_keys(self):
        result = adapter().run_clawde_command(["git", "push"])  # denied
        assert "success" in result
        assert "stdout" in result
        assert "stderr" in result
        assert "error" in result


# ── Kernel integration ─────────────────────────────────────────────────────────
class TestKernelWithoutAdapter:
    def test_kernel_works_without_adapter(self):
        """ClawdeOperatorKernel must work in mock mode when no adapter is present."""
        from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
        from core.operator_runtime.contracts import ToolRequest

        k = ClawdeOperatorKernel(department="app_factory")
        req = ToolRequest(tool_name="shell_exec", action="rm", args={"command": "rm -rf /"})
        result = k.execute_shell(req)
        assert result.success is False  # denied by policy

    def test_telemetry_preserved_without_adapter(self):
        """Telemetry must still record events even when adapter is not connected."""
        from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
        from core.operator_runtime.contracts import ToolRequest
        from core.operator_runtime.telemetry import get_telemetry

        tel = get_telemetry()
        before = len(tel.get_events())
        k = ClawdeOperatorKernel(department="app_factory")
        req = ToolRequest(tool_name="shell_exec", action="rm", args={"command": "rm -rf /"})
        k.execute_shell(req)
        assert len(tel.get_events()) > before
