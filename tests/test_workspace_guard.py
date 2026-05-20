"""
tests/test_workspace_guard.py
WorkspaceGuard — boundary enforcement tests
"""
import os
import pytest
from core.operator_runtime.workspace_guard import WorkspaceGuard


WORKSPACE = os.path.abspath(".")


def guard():
    return WorkspaceGuard(WORKSPACE)


class TestWorkspaceGuard:
    def test_read_normal_file_allowed(self):
        allowed, reason = guard().check_read("core/config.py")
        assert allowed is True

    def test_read_env_denied(self):
        allowed, reason = guard().check_read(".env")
        assert allowed is False

    def test_read_private_key_denied(self):
        allowed, reason = guard().check_read("id_rsa")
        assert allowed is False

    def test_write_inside_workspace_allowed(self):
        path = os.path.join(WORKSPACE, "output", "test_output.txt")
        allowed, reason = guard().check_write(path)
        assert allowed is True

    def test_write_outside_workspace_denied(self):
        allowed, reason = guard().check_write("/etc/hosts")
        assert allowed is False
        assert "outside workspace" in reason

    def test_write_env_denied_even_inside_workspace(self):
        path = os.path.join(WORKSPACE, ".env")
        allowed, reason = guard().check_write(path)
        assert allowed is False

    def test_write_wallet_denied(self):
        path = os.path.join(WORKSPACE, "wallet.json")
        allowed, reason = guard().check_write(path)
        assert allowed is False

    def test_delete_always_denied(self):
        allowed, reason = guard().check_delete("any_file.txt")
        assert allowed is False
        assert "approval" in reason.lower()

    def test_is_inside_workspace(self):
        assert guard().is_inside_workspace(os.path.join(WORKSPACE, "core", "config.py")) is True
        assert guard().is_inside_workspace("/etc/passwd") is False
