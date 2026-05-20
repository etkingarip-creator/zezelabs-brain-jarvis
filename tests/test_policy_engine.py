"""
tests/test_policy_engine.py
Policy Engine — unit tests (no Docker, no RabbitMQ, no external API)
"""
import pytest
from core.operator_runtime.policy_engine import PolicyEngine
from core.operator_runtime.contracts import RiskLevel, ApprovalStatus, ToolRequest


def policy(dept="general"):
    return PolicyEngine(department=dept)


# ── Shell ──────────────────────────────────────────────────────────────────────
class TestShellPolicy:
    def test_safe_git_status_allowed(self):
        d = policy().can_execute_shell("git status")
        assert d.allowed is True

    def test_rm_rf_denied(self):
        d = policy().can_execute_shell("rm -rf /tmp/test")
        assert d.allowed is False
        assert d.risk_level == RiskLevel.CRITICAL

    def test_eval_denied(self):
        d = policy().can_execute_shell("eval(user_input)")
        assert d.allowed is False

    def test_os_system_denied(self):
        d = policy().can_execute_shell("os.system('ls')")
        assert d.allowed is False

    def test_unknown_command_requires_approval(self):
        d = policy().can_execute_shell("custom_build_script.sh")
        assert d.allowed is False
        assert d.approval_status == ApprovalStatus.PENDING

    def test_ls_allowed(self):
        d = policy().can_execute_shell("ls -la")
        assert d.allowed is True


# ── File Operations ────────────────────────────────────────────────────────────
class TestFilePolicy:
    def test_read_normal_file_allowed(self):
        d = policy().can_read_file("core/config.py")
        assert d.allowed is True

    def test_read_env_file_denied(self):
        d = policy().can_read_file(".env")
        assert d.allowed is False
        assert d.risk_level == RiskLevel.CRITICAL

    def test_read_private_key_denied(self):
        d = policy().can_read_file("/home/user/.ssh/id_rsa")
        assert d.allowed is False

    def test_edit_inside_workspace_allowed(self):
        import os
        workspace = os.path.abspath(".")
        d = policy().can_edit_file("core/config.py", workspace)
        assert d.allowed is True

    def test_edit_outside_workspace_denied(self):
        d = policy().can_edit_file("/etc/passwd", "/home/project")
        assert d.allowed is False

    def test_edit_env_file_denied(self):
        import os
        workspace = os.path.abspath(".")
        d = policy().can_edit_file(".env", workspace)
        assert d.allowed is False


# ── Git ────────────────────────────────────────────────────────────────────────
class TestGitPolicy:
    def test_git_push_requires_approval(self):
        d = policy().can_push_git()
        assert d.allowed is False
        assert d.approval_status == ApprovalStatus.PENDING

    def test_force_push_always_denied(self):
        d = policy().can_force_push_git()
        assert d.allowed is False
        assert d.approval_status != ApprovalStatus.APPROVED


# ── Trading ────────────────────────────────────────────────────────────────────
class TestTradingPolicy:
    def test_live_trade_default_denied(self):
        d = policy("crypto_trading").can_trade_live()
        assert d.allowed is False

    def test_withdrawal_always_denied(self):
        d = policy("crypto_trading").can_withdraw()
        assert d.allowed is False

    def test_paper_trade_allowed_for_crypto_dept(self):
        d = policy("crypto_trading").can_trade_paper()
        assert d.allowed is True

    def test_paper_trade_denied_for_other_depts(self):
        d = policy("app_factory").can_trade_paper()
        assert d.allowed is False


# ── Deploy ─────────────────────────────────────────────────────────────────────
class TestDeployPolicy:
    def test_deploy_requires_approval(self):
        d = policy().can_deploy()
        assert d.allowed is False
        assert d.approval_status == ApprovalStatus.PENDING
