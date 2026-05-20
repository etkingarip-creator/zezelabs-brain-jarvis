"""
Zezelabs Holding OS — CryptoTrading Department Agent
Enforces strict risk policies: live_trade and withdrawal denied.
Runs paper trading simulations safely.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.operator_runtime.contracts import (
    AgentResult, RiskLevel,
)
from core.operator_runtime.policy_engine import PolicyEngine
from core.operator_runtime.telemetry import get_telemetry

DEPARTMENT = "crypto_trading"


class CryptoTradingAgent:
    """
    Autonomous Crypto Paper Trading Agent.
    Strictly restricted from live trading and withdrawals.
    """

    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        self.policy = policy_engine or PolicyEngine(department=DEPARTMENT)
        self.telemetry = get_telemetry()

    def run_paper_task(self, symbol: str, action: str, amount_usd: float, task_id: Optional[str] = None) -> AgentResult:
        """
        Produce a paper signal and update portfolio simulation.
        Always verifies with PolicyEngine before acting.
        """
        task_id = task_id or str(uuid.uuid4())
        
        # 1. Check policies
        paper_decision = self.policy.can_trade_paper()
        live_decision = self.policy.can_trade_live()
        withdraw_decision = self.policy.can_withdraw()

        if not paper_decision.allowed:
            self._log_telemetry(task_id, "paper_trade", "denied", paper_decision.reason, RiskLevel.MEDIUM)
            return self._fail(task_id, f"Paper trading denied: {paper_decision.reason}")

        # Ensure live/withdraw are explicitly logged as denied if they were ever requested, 
        # but here we just prove we checked them in the paper mode pipeline for safety logic
        
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
            }
        }

        output = (
            f"Paper Trade Executed\n"
            f"Symbol: {symbol}\n"
            f"Action: {action.upper()}\n"
            f"Amount: ${amount_usd}\n"
            f"Price: ${mock_price}\n"
            f"Policy: live_trade={live_decision.allowed}, withdrawal={withdraw_decision.allowed}"
        )

        # 4. Telemetry
        self._log_telemetry(task_id, "paper_trade", "success", None, RiskLevel.LOW)

        return AgentResult(
            task_id=task_id,
            department=DEPARTMENT,
            success=True,
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
