import pika
import json
import time

def publish_task():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='main_orchestrator_queue', durable=True)

    task_payload = {
        "id": "PHOENIX_LOGIN_001",
        "task": "FastAPI backend + React Tailwind login sayfası yaz, JWT auth olsun, Zezelabs dark academia estetiğinde",
        "timestamp": time.time(),
        "attempt": 1
    }

    channel.basic_publish(
        exchange='',
        routing_key='main_orchestrator_queue',
        body=json.dumps(task_payload),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    print(f" [x] Sent '{task_payload['task']}' to orchestrator")
    connection.close()

if __name__ == '__main__':
    publish_task()
