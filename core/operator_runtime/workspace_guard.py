"""
Zezelabs Operator Runtime — Workspace Guard
No writes outside workspace. No secret access.
"""
from __future__ import annotations
import os
import logging
from typing import Tuple

log = logging.getLogger("zom.workspace_guard")

_PROTECTED_PATTERNS = [
    ".env", ".env.local", ".env.production", ".env.secret",
    "id_rsa", "id_ed25519", ".pem", ".key", ".p12",
    "wallet.json", "mnemonic.txt", "keystore", "private_key",
    "secrets.json", "credentials.json",
]

_FORBIDDEN_PREFIXES = [
    os.path.expanduser("~/.ssh"),
    os.path.expanduser("~/.gnupg"),
    os.path.expanduser("~/.aws"),
]


class WorkspaceGuard:
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    def check_read(self, path: str) -> Tuple[bool, str]:
        abs_path = self._resolve(path)
        if self._is_secret(abs_path):
            return False, f"Protected file: {path}"
        if self._is_forbidden_prefix(abs_path):
            return False, f"Forbidden system path: {path}"
        return True, "Read allowed"

    def check_write(self, path: str) -> Tuple[bool, str]:
        abs_path = self._resolve(path)
        if self._is_secret(abs_path):
            return False, f"Protected file: {path}"
        if self._is_forbidden_prefix(abs_path):
            return False, f"Forbidden system path: {path}"
            
        # Allow Desktop writes
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            desktop_path = os.path.realpath(os.path.abspath(os.path.join(user_profile, "Desktop")))
            if abs_path.startswith(desktop_path):
                return True, "Write allowed"
                
        if not abs_path.startswith(self.workspace_root):
            return False, f"Write outside workspace denied: {path}"
        return True, "Write allowed"

    def check_delete(self, path: str) -> Tuple[bool, str]:
        return False, f"File deletion requires explicit human approval: {path}"

    def is_inside_workspace(self, path: str) -> bool:
        return self._resolve(path).startswith(self.workspace_root)

    @staticmethod
    def _resolve(path: str) -> str:
        return os.path.realpath(os.path.abspath(path))

    @staticmethod
    def _is_secret(abs_path: str) -> bool:
        lower = abs_path.lower()
        return any(p in lower for p in _PROTECTED_PATTERNS)

    @staticmethod
    def _is_forbidden_prefix(abs_path: str) -> bool:
        for prefix in _FORBIDDEN_PREFIXES:
            if abs_path.startswith(os.path.realpath(os.path.abspath(prefix))):
                return True
        return False
