# Runtime Side-Effect Audit

## High Risk (Live Execution & External Publishers)
- **`zeze_eng/sovereign_coder.py:45`** -> `git commit` (Executes git commit) - *Suggestion: Wrap in PolicyEngine validation.*
- **`zeze_eng/sovereign_coder.py:46`** -> `git push` (Currently commented out) - *Suggestion: Keep commented or gate behind `PolicyEngine.can_push_git()`.*
- **`backend/jarvis.py:257`** -> `subprocess.Popen` - *Suggestion: Avoid raw Popen for long-running scripts if Clawde adapter exists.*

## Medium Risk (Network calls)
- **`zeze_media/automation_agent.py:37`** -> `requests.post(target_url)`
- **`zeze_mystic/interpreter.py:52`** -> `requests.post(JARVIS_BRIDGE_URL)`
- **`live_matrix/backend/telemetry_server.py:88`** -> `pika.BlockingConnection`

## Policy Enforcement
- **`core/operator_runtime/adapters/clawde_process_adapter.py`** -> Validates `live_trade`, `withdrawal`, `git push` correctly.
- **`tests/test_clawde_process_adapter.py`** -> Test suite confirms that raw `shell=True` and `os.system` are banned.
