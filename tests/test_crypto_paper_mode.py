import pytest
from core.operator_runtime.contracts import AgentResult, DepartmentName
from departments.crypto_trading.agent import CryptoTradingAgent

def agent():
    return CryptoTradingAgent()

def test_crypto_paper_task_success():
    a = agent()
    result = a.run_paper_task(symbol="BTC/USDT", action="BUY", amount_usd=5000.0)
    
    assert isinstance(result, AgentResult)
    assert result.success is True
    assert result.department == "crypto_trading"
    assert len(result.tool_results) == 1
    
    signal = result.tool_results[0]
    assert signal["symbol"] == "BTC/USDT"
    assert signal["action"] == "BUY"
    assert signal["amount_usd"] == 5000.0
    assert "executed_price" in signal
    
    # Check policy checks were verified correctly
    checks = signal["policy_checks"]
    assert checks["paper_trade_allowed"] is True
    assert checks["live_trade_allowed"] is False
    assert checks["withdrawal_allowed"] is False

def test_crypto_telemetry():
    from core.operator_runtime.telemetry import get_telemetry
    
    tel = get_telemetry()
    before = len(tel.get_events())
    
    a = agent()
    a.run_paper_task("ETH/USDT", "SELL", 1000.0)
    
    assert len(tel.get_events()) > before
    
    events = tel.get_events()
    our_event = next(e for e in reversed(events) if e.tool_name == "crypto_agent" and e.action == "paper_trade")
    assert our_event.department == "crypto_trading"
    assert our_event.status == "success"
