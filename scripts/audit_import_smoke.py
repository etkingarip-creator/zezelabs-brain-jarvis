import importlib
import sys
import traceback

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
            importlib.import_module(mod)
            print(f"[OK] {mod}")
        except Exception as e:
            print(f"[FAIL] {mod}: {type(e).__name__} - {str(e)}")

if __name__ == '__main__':
    smoke_test()
