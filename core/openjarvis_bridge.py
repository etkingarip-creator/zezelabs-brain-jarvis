import json
import os
import sys
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
OPENJARVIS_ROOT = os.getenv("OPENJARVIS_ROOT", "C:/Users/Zezelabs2/OpenJarvis")


def run_jarvis_skill(skill_name: str, params: dict) -> str:
    """OpenJarvis CLI üzerinden skill çalıştırır."""
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-m", "openjarvis.cli",
             "skill", "run", skill_name, json.dumps(params)],
            cwd=OPENJARVIS_ROOT,
            capture_output=True, text=True, timeout=60
        )
        return result.stdout or result.stderr or "Skill tamamlandı (çıktı yok)."
    except FileNotFoundError:
        return "HATA: uv veya OpenJarvis bulunamadı."
    except Exception as e:
        return f"HATA: {e}"


def send_to_queue(queue: str, message: dict):
    """Belirtilen RabbitMQ kuyruğuna mesaj gönderir."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    ch = conn.channel()
    ch.queue_declare(queue=queue, durable=True)
    ch.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()
    print(f"[OpenJarvisBridge] 📤 '{queue}' kuyruğuna gönderildi.")


def dispatch_skill_to_queue(skill_name: str, params: dict, target_queue: str):
    """Skill çalıştırır ve sonucu kuyruğa gönderir."""
    print(f"[OpenJarvisBridge] Skill '{skill_name}' çalıştırılıyor...")
    result = run_jarvis_skill(skill_name, params)
    payload = {
        "skill": skill_name,
        "params": params,
        "result": result,
        "source": "openjarvis_bridge"
    }
    send_to_queue(target_queue, payload)
    return result
