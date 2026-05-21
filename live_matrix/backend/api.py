from fastapi import FastAPI
from live_matrix.backend.zeze_guard_provider import ZezeGuardProvider

app = FastAPI(title="Zezelabs Live Matrix API")
provider = ZezeGuardProvider()

@app.get("/api/zeze-guard/snapshot")
def get_snapshot():
    return provider.get_zeze_guard_snapshot()

@app.get("/api/zeze-guard/loops")
def get_loops():
    return provider.get_loop_alerts()

@app.get("/api/zeze-guard/roi")
def get_roi():
    return provider.get_roi_summary()

@app.get("/api/zeze-guard/alerts")
def get_alerts():
    return provider.get_shadow_ceo_alerts()
