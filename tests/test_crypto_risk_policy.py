"""
tests/test_crypto_risk_policy.py
Crypto department — risk policy enforcement tests
"""
import pytest
from core.operator_runtime.policy_engine import PolicyEngine
from core.operator_runtime.contracts import ApprovalStatus


def crypto_policy():
    return PolicyEngine(department="crypto_trading")


class TestCryptoRiskPolicy:
    def test_live_trading_default_denied(self):
        d = crypto_policy().can_trade_live()
        assert d.allowed is False

    def test_withdrawal_always_denied(self):
        d = crypto_policy().can_withdraw()
        assert d.allowed is False

    def test_paper_trading_allowed(self):
        d = crypto_policy().can_trade_paper()
        assert d.allowed is True

    def test_git_push_denied_for_crypto(self):
        d = crypto_policy().can_push_git()
        assert d.allowed is False
        assert d.approval_status == ApprovalStatus.PENDING

    def test_deploy_denied_for_crypto(self):
        d = crypto_policy().can_deploy()
        assert d.allowed is False

    def test_force_push_denied_for_crypto(self):
        d = crypto_policy().can_force_push_git()
        assert d.allowed is False

    def test_shell_rm_denied_for_crypto(self):
        d = crypto_policy().can_execute_shell("rm -rf /data")
        assert d.allowed is False


"""
tests/test_app_factory_manifest.py
App factory department manifest validation tests
"""
import os
import yaml


MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "departments", "app_factory", "manifest.yaml"
)


class TestAppFactoryManifest:
    def _load(self):
        with open(MANIFEST_PATH, "r") as f:
            return yaml.safe_load(f)

    def test_manifest_exists(self):
        assert os.path.exists(MANIFEST_PATH)

    def test_department_name(self):
        m = self._load()
        assert m["department"] == "app_factory"

    def test_queue_name(self):
        m = self._load()
        assert m["queue"] == "zeze_app_factory_queue"

    def test_file_edit_allowed(self):
        m = self._load()
        assert "file_edit" in m["allowed_tools"]

    def test_live_trade_forbidden(self):
        m = self._load()
        assert "live_trade" in m["forbidden_tools"]

    def test_withdrawal_forbidden(self):
        m = self._load()
        assert "withdrawal" in m["forbidden_tools"]

    def test_git_push_requires_approval(self):
        m = self._load()
        assert "git_push" in m["approval_required"]

    def test_deploy_requires_approval(self):
        m = self._load()
        assert "deploy" in m["approval_required"]
