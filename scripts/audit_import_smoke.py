import importlib
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import time

MODULES = [
    "backend.jarvis",
    "backend.QueryEngine",
    "core.operator_runtime.policy_engine",
    "core.operator_runtime.clawde_kernel",
    "core.zeze_guard.anti_loop",
    "core.zeze_guard.roi_tracker",
    "core.zeze_academy.trace_logger",
    "core.zeze_academy.budget_guard",
    "departments.app_factory.agent",
    "departments.crypto_trading.agent",
    "departments.zeze_aro.agent",
    "departments.media_factory.agent",
    "live_matrix.backend.zeze_guard_provider",
    "live_matrix.backend.api"
]

def smoke_test():
    for mod in MODULES:
        try:
            start = time.time()
            importlib.import_module(mod)
            elapsed = time.time() - start
            print(f"[OK] {mod} {elapsed:.3f}s")
        except Exception as e:
            print(f"[FAIL] {mod}: {type(e).__name__} - {str(e)}")

if __name__ == '__main__':
    smoke_test()
