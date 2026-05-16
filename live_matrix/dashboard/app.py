import psutil
import json
import os
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="ZOM Tactical Command API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PIXEL_LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pixel_agents_logs")
STATE_FILE = os.path.join(PIXEL_LOGS_DIR, "dashboard_state.json")

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"total_tasks": 0, "active_agents": {}, "last_messages": [], "token_spent_estimate": 0}

@app.get("/api/state")
def get_state():
    state = load_state()
    
    # HARDCORE METRICS (Simulated if not present in state file)
    # T/s (Token per second) - Fluctuates based on active tasks
    base_tps = len(state.get("active_agents", {})) * random.uniform(15.0, 45.0)
    state["token_per_sec"] = round(base_tps + random.uniform(0, 10), 2)
    
    # AEC (Agent Efficiency Coefficient) - Target 0.95
    state["agent_efficiency"] = round(random.uniform(0.88, 0.98), 3)
    
    # GPU Core (Tulpar simulation)
    gpu_base_temp = 55.0 + (len(state.get("active_agents", {})) * 5)
    state["gpu_temp"] = round(gpu_base_temp + random.uniform(-2, 2), 1)
    state["vram_usage"] = round(random.uniform(12.5, 23.8), 1) # GB
    
    # RabbitMQ Queue
    state["rabbitmq_queue_size"] = random.randint(0, 15) if state.get("total_tasks", 0) > 0 else 0
    
    # System
    state["cpu_percent"] = psutil.cpu_percent()
    state["ram_percent"] = psutil.virtual_memory().percent
    
    # Generate some fake terminal statuses for agents if they don't have them
    for agent_key in state.get("active_agents", {}).keys():
        if isinstance(state["active_agents"][agent_key], dict) and "status" not in state["active_agents"][agent_key]:
            state["active_agents"][agent_key]["status"] = random.choice(["COMPACTING MEMORY...", "COMMITTING HASH...", "QUERYING DB...", "AWAITING RABBITMQ"])
    
    return state

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8502)
