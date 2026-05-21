import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient
from live_matrix.backend.zeze_guard_provider import ZezeGuardProvider
import json

def seed_dogfood_data():
    print("Seeding ZEZE-GUARD Mock Dogfood Data...")
    
    # 1. AntiLoopEngine Seed
    anti_loop = AntiLoopEngine()
    for _ in range(3):
        anti_loop.record_event("live_matrix_agent", "task_999", "git_push", "error: hook declined")
    
    # 2. ROITracker Seed
    roi = ROITracker()
    roi.record_cost("live_matrix_agent", "task_999", "deepseek-coder", 1000, 500, 0.15)
    roi.record_cost("zeze_aro_agent", "task_888", "hermes-3", 2000, 1000, 0.30)
    
    roi.record_outcome("live_matrix_agent", "task_999", "task", False)
    roi.record_outcome("zeze_aro_agent", "task_888", "task", True)
    
    # 3. ShadowCEOAlert Seed
    ceo = ShadowCEOAlertClient()
    ceo.send_alert("Loop Detected in Live Matrix", "Agent stuck on git_push hook.", severity="critical")
    
    # 4. Snapshot check
    provider = ZezeGuardProvider()
    snapshot = provider.get_zeze_guard_snapshot()
    
    print("Seeding Complete. Snapshot output:")
    print(json.dumps(snapshot, indent=2))

if __name__ == "__main__":
    seed_dogfood_data()
