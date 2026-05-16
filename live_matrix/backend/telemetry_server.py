import asyncio
import websockets
import pika
import json
import os
import threading
import datetime

# ZOM -> PIXEL AGENTS & STREAMLIT BRIDGE
PIXEL_LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pixel_agents_logs")
os.makedirs(PIXEL_LOGS_DIR, exist_ok=True)
SESSION_FILE = os.path.join(PIXEL_LOGS_DIR, "zom_session.jsonl")
DASHBOARD_STATE_FILE = os.path.join(PIXEL_LOGS_DIR, "dashboard_state.json")

# Global state for dashboard
system_state = {
    "total_tasks": 0,
    "active_agents": {},
    "last_messages": [],
    "token_spent_estimate": 0
}

def update_dashboard_state(data):
    target = data.get("target_agent", "system")
    msg = data.get("message", "")
    
    system_state["total_tasks"] += 1
    system_state["active_agents"][target] = datetime.datetime.utcnow().isoformat()
    system_state["last_messages"].insert(0, f"[{target.upper()}] {msg}")
    system_state["last_messages"] = system_state["last_messages"][:10]
    
    # Kaba token tahmini
    system_state["token_spent_estimate"] += len(msg) * 1.5
    
    with open(DASHBOARD_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(system_state, f)

def bridge_to_pixel_agents(data):
    """
    RabbitMQ'dan gelen telemetriyi Claude Code JSONL formatina cevirir.
    Pixel Agents (VS Code/Cursor eklentisi) bu dosyayi okuyarak ofis simulasyonunu canlandirir.
    """
    origin = data.get("origin_agent", "system")
    target = data.get("target_agent", "system")
    msg = data.get("message", "Processing task...")
    
    # 1. User prompt (Sistemin ajani tetiklemesi)
    user_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "message": {"role": "user", "content": [{"type": "text", "text": f"[{target}] {msg}"}]}
    }
    
    # 2. Assistant (Ajanin otonom harekete gecmesi)
    content = []
    if "dev" in origin or "dev" in target:
        content.append({"type": "tool_use", "name": "Bash", "input": {"command": "coding..."}})
    elif "reviewer" in origin or "reviewer" in target:
        content.append({"type": "tool_use", "name": "View", "input": {"file": "reviewing..."}})
    else:
        content.append({"type": "text", "text": msg})
        
    assistant_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "message": {"role": "assistant", "content": content}
    }
    
    with open(SESSION_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(user_entry) + "\n")
        f.write(json.dumps(assistant_entry) + "\n")

# Connected WebSocket clients
connected_clients = set()

# Set by main() — shared between threads
ws_loop: asyncio.AbstractEventLoop | None = None

def rabbitmq_listener():
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", 5672))
    user = os.getenv("RABBITMQ_USER", "admin")
    pw = os.getenv("RABBITMQ_PASS", "admin123")
    
    credentials = pika.PlainCredentials(user, pw)
    
    while True:
        try:
            print(f"[Telemetry] Connecting to RabbitMQ at {host}:{port}...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host, port=port, credentials=credentials)
            )
            channel = connection.channel()
            
            # Ensure exchange exists
            channel.exchange_declare(exchange='telemetry_exchange', exchange_type='fanout', durable=True)
            
            # Create exclusive queue for this telemetry instance
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            
            channel.queue_bind(exchange='telemetry_exchange', queue=queue_name)
            print("[Telemetry] Waiting for live data on telemetry_exchange...")
            
            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    print(f"[Telemetry] Broadcast: {data.get('queue')}")
                    # Push to async event loop thread safely
                    asyncio.run_coroutine_threadsafe(
                        broadcast_async(data),
                        ws_loop
                    )
                    
                    # Pixel Agents JSONL Bridge
                    bridge_to_pixel_agents(data)
                    
                    # Streamlit Dashboard State Update
                    update_dashboard_state(data)

                except Exception as e:
                    print(f"Error parsing telemetry: {e}")
                    
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            channel.start_consuming()
            
        except Exception as e:
            print(f"[Telemetry] RabbitMQ connection error: {e}. Retrying in 3s...")
            import time
            time.sleep(3)

async def broadcast_async(data):
    if connected_clients:
        message = json.dumps(data)
        # Use gather to send to all connected clients concurrently
        await asyncio.gather(*(client.send(message) for client in connected_clients), return_exceptions=True)

async def ws_handler(websocket):
    print(f"[WS] Client connected")
    connected_clients.add(websocket)
    try:
        # We don't expect messages from the client, just keep the connection open
        async for msg in websocket:
            pass
    except Exception as e:
        print(f"[WS] Connection error: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"[WS] Client disconnected")

async def main():
    global ws_loop
    ws_loop = asyncio.get_running_loop()
    
    # Start RabbitMQ listener in a separate thread
    mq_thread = threading.Thread(target=rabbitmq_listener, daemon=True)
    mq_thread.start()
    
    print("[Telemetry] WebSocket Server listening on port 8001")
    async with websockets.serve(ws_handler, "0.0.0.0", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
