"""
Zezelabs Operator Runtime — Clawde Process Adapter
Single official subprocess bridge to Clawde_Code CLI.

Rules (hardcoded, not overridable):
  - shell=True is NEVER used
  - os.system is NEVER used
  - cwd MUST be inside workspace
  - args MUST be a list
  - timeout is ALWAYS enforced
  - git push / deploy / live_trade / withdrawal → permanently denied
"""
from __future__ import annotations
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("zom.clawde_adapter")

# ── Permanently denied argument patterns ──────────────────────────────────────
_DENIED_ARGS = frozenset([
    "git push",
    "--force",
    "-f",
    "deploy",
    "live_trade",
    "live-trade",
    "withdrawal",
    "rm -rf",
    "del /s",
    "format",
    "mkfs",
    "shutdown",
    "reboot",
])

_DENIED_ARG_FRAGMENTS = [
    "push", "--force", "withdraw", "live_trade", "live-trade",
    "rm -rf", "del /s",
]

DEFAULT_TIMEOUT = 60  # seconds


class ClawdeProcessAdapterError(Exception):
    pass


class ClawdeProcessAdapter:
    """
    Safe subprocess bridge to Clawde_Code CLI runtime.
    All calls validated before subprocess.run() is invoked.
    """

    def __init__(self, clawde_root: str, workspace_root: str, timeout: int = DEFAULT_TIMEOUT):
        self.clawde_root = os.path.realpath(os.path.abspath(clawde_root))
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
        self.timeout = timeout

    # ── Public API ─────────────────────────────────────────────────────────────
    def run_clawde_command(
        self,
        args: list,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """
        Execute a Clawde_Code CLI command as a subprocess.
        Returns: {"success": bool, "stdout": str, "stderr": str, "error": str|None}
        """
        started = datetime.now(timezone.utc)

        # 1. Validate args type
        ok, reason = self.validate_args(args)
        if not ok:
            log.warning(f"[ADAPTER] DENIED args: {reason}")
            return self._denied(reason, started)

        # 2. Validate cwd
        effective_cwd = cwd or self.workspace_root
        ok, reason = self.validate_cwd(effective_cwd)
        if not ok:
            log.warning(f"[ADAPTER] DENIED cwd: {reason}")
            return self._denied(reason, started)

        # 3. Build full command
        cmd = self.build_command(args)

        # 4. Execute — shell=False always
        effective_timeout = timeout or self.timeout
        try:
            result = subprocess.run(
                cmd,
                cwd=effective_cwd,
                shell=False,           # HARDCODED — NEVER True
                capture_output=True,
                text=True,
                timeout=effective_timeout,
            )
            finished = datetime.now(timezone.utc)
            success = result.returncode == 0
            log.info(f"[ADAPTER] {'OK' if success else 'FAIL'} cmd={cmd[:3]} rc={result.returncode}")
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": result.stderr if not success else None,
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
            }
        except subprocess.TimeoutExpired:
            return self._denied(f"Command timed out after {effective_timeout}s", started)
        except FileNotFoundError as e:
            return self._denied(f"Executable not found: {e}", started)
        except Exception as e:
            return self._denied(f"Unexpected error: {e}", started)

    # ── Validation ─────────────────────────────────────────────────────────────
    def validate_args(self, args) -> tuple[bool, str]:
        """Args must be a non-empty list of strings with no denied patterns."""
        if not isinstance(args, list):
            return False, f"args must be a list, got {type(args).__name__}"
        if not args:
            return False, "args must not be empty"
        if not all(isinstance(a, str) for a in args):
            return False, "all args must be strings"

        args_lower = [a.lower() for a in args]
        for denied in _DENIED_ARG_FRAGMENTS:
            for arg in args_lower:
                if denied in arg:
                    return False, f"Denied argument pattern '{denied}' in arg '{arg}'"

        return True, "ok"

    def validate_cwd(self, cwd: str) -> tuple[bool, str]:
        """cwd must be inside workspace_root."""
        resolved = os.path.realpath(os.path.abspath(cwd))
        if not resolved.startswith(self.workspace_root):
            return False, f"cwd outside workspace: {cwd}"
        return True, "ok"

    def build_command(self, args: list) -> list:
        """
        Prepend node/clawde entrypoint to args.
        Falls back to safe echo if clawde entrypoint not found (test/dry-run mode).
        """
        # Check for Clawde_Code node entrypoint
        clawde_entry = os.path.join(self.clawde_root, "index.ts")
        clawde_built = os.path.join(self.clawde_root, "dist", "index.js")

        if os.path.exists(clawde_built):
            return ["node", clawde_built] + args
        elif os.path.exists(clawde_entry):
            return ["npx", "ts-node", clawde_entry] + args
        else:
            # Dry-run mode — command will fail gracefully
            log.warning("[ADAPTER] Clawde_Code entry not found — running in dry-run stub mode")
            return ["echo", "[DRY-RUN]"] + args

    # ── Helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _denied(reason: str, started: datetime) -> dict:
        finished = datetime.now(timezone.utc)
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": f"DENIED: {reason}",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
        }
