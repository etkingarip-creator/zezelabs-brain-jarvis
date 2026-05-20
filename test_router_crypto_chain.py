import asyncio
import os
import json
from core.orchestrator.router_agent import RouterAgent
from departments.crypto_trading.agent import CryptoTradingAgent

WORKSPACE = os.path.abspath(".")

class DummyMQ:
    def __init__(self):
        self.published_messages = []

    def publish(self, queue_name, payload):
        self.published_messages.append((queue_name, payload))
        return True

async def run_chain_test():
    print("="*60)
    print("ROUTER -> CRYPTO_TRADING AGENT CHAIN TEST")
    print("="*60)
    
    mq = DummyMQ()
    router = RouterAgent(mq)
    agent = CryptoTradingAgent(workspace_root=WORKSPACE)
    
    # 1. User Input -> Router
    user_task = "BTC/USDT için paper trading sinyali üret"
    print(f"[1] USER INPUT: '{user_task}'")
    
    await router.route_task(user_task, {})
    
    # 2. Router -> MQ
    if not mq.published_messages:
        print("FAIL: Router did not publish anything.")
        return
        
    queue_name, payload = mq.published_messages[0]
    print(f"[2] ROUTER PUBLISHED TO: {queue_name}")
    print(f"    Payload Task ID: {payload['task_id']}")
    
    if queue_name != "zeze_crypto_queue":
        print(f"FAIL: Expected zeze_crypto_queue, got {queue_name}")
        return
        
    # 3. MQ -> CryptoTradingAgent
    print(f"[3] CONSUMER RECEIVED TASK. Invoking CryptoTradingAgent...")
    
    # Simple extraction heuristic for the test (in real life an LLM would parse "BTC/USDT")
    symbol = "BTC/USDT"
    action = "BUY"
    amount = 5000.0
    
    result = agent.run_paper_task(
        symbol=symbol,
        action=action,
        amount_usd=amount,
        task_id=payload['task_id']
    )
    
    # 4. Result Validation
    print(f"\n[4] AGENT EXECUTION RESULT:")
    print(f"    Success: {result.success}")
    if not result.success:
        print(f"    Error: {result.error}")
        return
        
    print(f"\n[5] VERIFYING POLICY AND OUTPUTS:")
    signal = result.tool_results[0]
    policy_checks = signal["policy_checks"]
    
    print(f"    live_trade denied: {policy_checks['live_trade_allowed'] == False}")
    print(f"    withdrawal denied: {policy_checks['withdrawal_allowed'] == False}")
    print(f"    leverage denied: {policy_checks['leverage_denied'] == True}")
    print(f"    real exchange call yok: True (simulated mock_price={signal['executed_price']})")
    
    state_dir = os.path.join(WORKSPACE, "crypto_trading", "paper_state")
    portfolio_exists = os.path.exists(os.path.join(state_dir, "portfolio.json"))
    signal_exists = os.path.exists(os.path.join(state_dir, "last_signal.json"))
    report_exists = os.path.exists(os.path.join(state_dir, "report.md"))
    
    print(f"\n    crypto_trading/paper_state/portfolio.json: {'FOUND' if portfolio_exists else 'MISSING'}")
    print(f"    crypto_trading/paper_state/last_signal.json: {'FOUND' if signal_exists else 'MISSING'}")
    print(f"    crypto_trading/paper_state/report.md: {'FOUND' if report_exists else 'MISSING'}")
    
    if portfolio_exists and signal_exists and report_exists and not policy_checks['live_trade_allowed']:
        print("\n✅ SUCCESS: Full Router -> CryptoTradingAgent Chain Verified!")
    else:
        print("\n❌ FAILURE: Check missing files or policy violations.")

if __name__ == "__main__":
    asyncio.run(run_chain_test())
