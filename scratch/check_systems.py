import httpx
import json
import pika
import os

results = {}

# Check Ollama
try:
    resp = httpx.get("http://localhost:11434/api/tags", timeout=2)
    if resp.status_code == 200:
        results["ollama"] = "Online"
        results["models"] = [m["name"] for m in resp.json().get("models", [])]
    else:
        results["ollama"] = f"Error {resp.status_code}"
except Exception as e:
    results["ollama"] = f"Offline ({e})"

# Check RabbitMQ
try:
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5672, heartbeat=2))
    results["rabbitmq"] = "Online"
    conn.close()
except Exception as e:
    results["rabbitmq"] = f"Offline ({e})"

# Check Env
results["gemini_key"] = "Set" if os.getenv("GEMINI_API_KEY") else "Missing"

with open("system_check_results.json", "w") as f:
    json.dump(results, f, indent=2)
