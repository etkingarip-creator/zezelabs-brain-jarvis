"""
Zezelabs Holding OS — CryptoTrading Department Agent
Enforces strict risk policies: live_trade and withdrawal denied.
Runs paper trading simulations safely.
"""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.operator_runtime.contracts import (
    AgentResult, RiskLevel, ToolRequest, DepartmentName
)
from core.operator_runtime.policy_engine import PolicyEngine
from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
from core.operator_runtime.telemetry import get_telemetry

DEPARTMENT = "crypto_trading"


class CryptoTradingAgent:
    """
    Autonomous Crypto Paper Trading Agent.
    Strictly restricted from live trading and withdrawals.
    """

    def __init__(
        self,
        workspace_root: str,
        policy_engine: Optional[PolicyEngine] = None,
        kernel: Optional[ClawdeOperatorKernel] = None,
    ):
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
        self.department = DepartmentName.CRYPTO_TRADING
        self.policy = policy_engine or PolicyEngine(department=DEPARTMENT)
        self.kernel = kernel or ClawdeOperatorKernel(
            department=DEPARTMENT,
            workspace_root=self.workspace_root,
        )
        self.telemetry = get_telemetry()

    def run_paper_task(self, symbol: str, action: str, amount_usd: float, task_id: Optional[str] = None) -> AgentResult:
        """
        Produce a paper signal and update portfolio simulation.
        Always verifies with PolicyEngine before acting.
        """
        task_id = task_id or str(uuid.uuid4())
        state_dir = os.path.join(self.workspace_root, "crypto_trading", "paper_state")
        
        # 1. Check policies
        paper_decision = self.policy.can_trade_paper()
        live_decision = self.policy.can_trade_live()
        withdraw_decision = self.policy.can_withdraw()

        if not paper_decision.allowed:
            self._log_telemetry(task_id, "paper_trade", "denied", paper_decision.reason, RiskLevel.MEDIUM)
            return self._fail(task_id, f"Paper trading denied: {paper_decision.reason}")
        
        # 2. Simulate Market Data (Mock)
        mock_price = 65000.0 if "BTC" in symbol else 3000.0
        mock_quantity = amount_usd / mock_price

        # 3. Create signal payload
        signal = {
            "task_id": task_id,
            "department": DEPARTMENT,
            "symbol": symbol,
            "action": action.upper(),
            "amount_usd": amount_usd,
            "executed_price": mock_price,
            "executed_quantity": mock_quantity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "paper_trade",
            "policy_checks": {
                "paper_trade_allowed": paper_decision.allowed,
                "live_trade_allowed": live_decision.allowed,
                "withdrawal_allowed": withdraw_decision.allowed,
                "leverage_denied": True  # Always denied in paper default
            }
        }

        portfolio = {
            "balance_usd": 100000.0 - (amount_usd if action.upper() == "BUY" else 0.0),
            "holdings": {
                symbol: mock_quantity if action.upper() == "BUY" else 0.0
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        report = f"""# Crypto Paper Trade Report
**Symbol:** {symbol}
**Action:** {action.upper()}
**Amount:** ${amount_usd}
**Executed Price:** ${mock_price}
**Status:** SUCCESS (Paper Mode)
**Live Trade:** {'ALLOWED' if live_decision.allowed else 'DENIED'}
**Withdrawal:** {'ALLOWED' if withdraw_decision.allowed else 'DENIED'}
**Leverage:** DENIED
"""

        files_to_create = {
            "last_signal.json": json.dumps(signal, indent=2),
            "portfolio.json": json.dumps(portfolio, indent=2),
            "report.md": report
        }

        created_files = []
        errors = []

        for rel_path, content in files_to_create.items():
            abs_path = os.path.join(state_dir, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            req = ToolRequest(
                tool_name="file_edit",
                action=f"create {rel_path}",
                task_id=task_id,
                department=DEPARTMENT,
                args={"path": abs_path, "content": content},
                risk_level=RiskLevel.LOW,
            )
            result = self.kernel.edit_file(req)

            if result.success:
                created_files.append(abs_path)
            else:
                errors.append(f"{rel_path}: {result.error}")

        success = len(errors) == 0
        output = (
            f"Paper Trade Executed at {state_dir}\n"
            f"Files: {len(created_files)}\n"
            + "\n".join(f"  ✅ {f}" for f in created_files)
        )
        if errors:
            output += "\nErrors:\n" + "\n".join(f"  ❌ {e}" for e in errors)

        # 4. Telemetry
        self._log_telemetry(task_id, "paper_trade", "success" if success else "partial_error", None, RiskLevel.LOW)

        return AgentResult(
            task_id=task_id,
            department=DEPARTMENT,
            success=success,
            output=output,
            tool_results=[signal]
        )

    def _log_telemetry(self, task_id: str, action: str, status: str, error: Optional[str], risk: RiskLevel):
        self.telemetry.record_execution(
            task_id=task_id,
            department=DEPARTMENT,
            tool_name="crypto_agent",
            action=action,
            status=status,
            risk_level=risk.value,
            error=error,
            finished_at=datetime.now(timezone.utc)
        )

    def _fail(self, task_id: str, reason: str) -> AgentResult:
        return AgentResult(
            task_id=task_id,
            department=DEPARTMENT,
            success=False,
            output=f"Task failed: {reason}",
            error=reason
        )
