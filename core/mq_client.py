import json
import logging
import os
import sys
import time
import asyncio
from typing import Optional, Callable, Dict, Any
from datetime import datetime

try:
    import pika
    from pika.adapters.asyncio_connection import AsyncioConnection
    HAS_PIKA = True
except ImportError:
    HAS_PIKA = False

class MQClient:
    """
    Unified Message Queue Client - PRODUCTION GRADE (v11.0)
    Supports RabbitMQ (Production) and File-based fallback (Development).
    Features parallel synchronous and asynchronous connections, dead-letter queues (DLQs),
    exchange declaring, fallback polling, and a 5-minute circuit breaker.
    """
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        enable: Optional[bool] = None,
        max_retries: Optional[int] = None,
    ):
        self.host = host or os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(port or os.getenv("RABBITMQ_PORT", "5672"))
        self.user = user or os.getenv("RABBITMQ_USER", "guest")
        self.password = password if password is not None else os.getenv("RABBITMQ_PASS", "guest")
        self.enable = enable if enable is not None else os.getenv("ZOM_ENABLE_RABBITMQ", "false").lower() == "true"
        self.max_retries = int(max_retries if max_retries is not None else os.getenv("ZOM_MAX_RETRIES", "3"))
        
        self.logger = logging.getLogger("zom.mq")
        self.connection = None
        self.channel = None
        self.connected = False
        
        # Async-specific
        self.async_connection = None
        self.async_channel = None
        self.async_connected = False
        
        # Fallback config
        self.fallback_dir = os.path.join(os.getcwd(), "scratch", "queues")
        os.makedirs(self.fallback_dir, exist_ok=True)
        
        # Circuit Breaker config (5 minutes)
        self.circuit_broken = False
        self.circuit_broken_until = 0.0
        self.circuit_break_duration = 300.0  # 5 minutes

    def connect(self) -> bool:
        """SYNCHRONOUS connection with exponential backoff and circuit breaker protection"""
        if not self.enable:
            self._setup_fallback_mode()
            return False
            
        if not HAS_PIKA:
            self.logger.warning("⚠️ Pika not installed. Using local fallback mode.")
            self._setup_fallback_mode()
            return False
            
        # Circuit Breaker Check
        if self.circuit_broken:
            if time.time() < self.circuit_broken_until:
                self.logger.warning("🔌 Circuit breaker is ACTIVE. Skipping connection and using fallback.")
                self._setup_fallback_mode()
                return False
            else:
                self.circuit_broken = False
                
        for attempt in range(self.max_retries):
            try:
                credentials = pika.PlainCredentials(self.user, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials,
                    connection_attempts=3,
                    retry_delay=2,
                    socket_timeout=5,
                    heartbeat=600
                )
                
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.channel.basic_qos(prefetch_count=1)
                
                self.connected = True
                self.logger.info(f"✅ Connected to RabbitMQ at {self.host}:{self.port}")
                return True
                
            except pika.exceptions.AMQPConnectionError as e:
                wait_time = 2 ** attempt
                self.logger.warning(
                    f"❌ RabbitMQ connection failed (attempt {attempt+1}/{self.max_retries}). "
                    f"Retrying in {wait_time}s... Error: {e}"
                )
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"❌ Unexpected connection error: {e}")
                break
                
        # All attempts failed -> Trip circuit breaker
        self.circuit_broken = True
        self.circuit_broken_until = time.time() + self.circuit_break_duration
        self.logger.error(f"🔌 RabbitMQ failed. Tripping circuit breaker for {self.circuit_break_duration}s. Using fallback.")
        self._setup_fallback_mode()
        return False
        
    async def connect_async(self) -> bool:
        """ASYNCHRONOUS connection using pika AsyncioConnection"""
        if not self.enable:
            self._setup_fallback_mode()
            return False
            
        if not HAS_PIKA:
            self.logger.warning("⚠️ Pika not installed. Using local fallback mode.")
            self._setup_fallback_mode()
            return False
            
        # Circuit Breaker Check
        if self.circuit_broken:
            if time.time() < self.circuit_broken_until:
                self.logger.warning("🔌 Circuit breaker is ACTIVE. Skipping async connection and using fallback.")
                self._setup_fallback_mode()
                return False
            else:
                self.circuit_broken = False
                
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            
            def on_open(connection):
                self.async_connection = connection
                connection.channel(on_open_callback=on_channel_open)
                
            def on_channel_open(channel):
                self.async_channel = channel
                self.async_connected = True
                self.logger.info(f"✅ Async connected to RabbitMQ at {self.host}:{self.port}")
                if not future.done():
                    future.set_result(True)
                    
            def on_open_error(connection, err):
                self.logger.error(f"❌ Async open error: {err}")
                if not future.done():
                    future.set_exception(err)
                    
            def on_close(connection, reason):
                self.logger.warning(f"🔌 Async connection closed: {reason}")
                self.async_connected = False
                
            self.async_connection = AsyncioConnection(
                parameters,
                on_open_callback=on_open,
                on_open_error_callback=on_open_error,
                on_close_callback=on_close
            )
            
            await asyncio.wait_for(future, timeout=10.0)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Async MQ connection failed: {e}")
            self.circuit_broken = True
            self.circuit_broken_until = time.time() + self.circuit_break_duration
            self._setup_fallback_mode()
            return False

    def _setup_fallback_mode(self):
        """Setup local file-based queue fallback"""
        self.fallback_dir = os.path.join(os.getcwd(), "scratch", "queues")
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.logger.info(f"📁 Fallback mode enabled. Queue directory: {self.fallback_dir}")

    def declare_queue(self, queue_name: str) -> bool:
        """Declare a durable queue"""
        if not queue_name:
            return False
        if self.connected and self.channel:
            try:
                self.channel.queue_declare(queue=queue_name, durable=True)
                return True
            except Exception as e:
                self.logger.error(f"❌ Failed to declare queue '{queue_name}': {e}")
                return False
        return True

    async def declare_queue_async(self, queue_name: str) -> bool:
        """Declare a durable queue asynchronously"""
        if not queue_name:
            return False
        if self.async_connected and self.async_channel:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            
            def on_declare(frame):
                if not future.done():
                    future.set_result(True)
                    
            try:
                self.async_channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    callback=on_declare
                )
                await asyncio.wait_for(future, timeout=5.0)
                return True
            except Exception as e:
                self.logger.error(f"❌ Async failed to declare queue '{queue_name}': {e}")
                return False
        return True

    def declare_exchange(self, exchange_name: str, exchange_type: str = "direct") -> bool:
        """Declare an exchange"""
        if not exchange_name:
            return False
        if self.connected and self.channel:
            try:
                self.channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
                return True
            except Exception as e:
                self.logger.error(f"❌ Failed to declare exchange '{exchange_name}': {e}")
                return False
        return True

    async def declare_exchange_async(self, exchange_name: str, exchange_type: str = "direct") -> bool:
        """Declare an exchange asynchronously"""
        if not exchange_name:
            return False
        if self.async_connected and self.async_channel:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            
            def on_declare(frame):
                if not future.done():
                    future.set_result(True)
            try:
                self.async_channel.exchange_declare(
                    exchange=exchange_name,
                    exchange_type=exchange_type,
                    durable=True,
                    callback=on_declare
                )
                await asyncio.wait_for(future, timeout=5.0)
                return True
            except Exception as e:
                self.logger.error(f"❌ Async failed to declare exchange '{exchange_name}': {e}")
                return False
        return True

    def publish(self, queue_or_exchange: str, message: Dict[str, Any], routing_key: Optional[str] = None) -> bool:
        """Publish message synchronously. Supports both queue-based and exchange/routing_key-based publishing."""
        if not queue_or_exchange:
            self.logger.error("❌ Queue or exchange name cannot be empty")
            return False
            
        msg_str = json.dumps(message, default=str)
        exchange = ""
        actual_routing_key = queue_or_exchange
        
        if routing_key is not None:
            exchange = queue_or_exchange
            actual_routing_key = routing_key
            
        if self.connected and self.channel:
            try:
                if not routing_key:
                    self.channel.queue_declare(queue=actual_routing_key, durable=True)
                    
                self.channel.basic_publish(
                    exchange=exchange,
                    routing_key=actual_routing_key,
                    body=msg_str,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                        content_type='application/json'
                    )
                )
                return True
            except Exception as e:
                self.logger.warning(f"⚠️ RabbitMQ publish failed: {e}. Falling back.")
                self.connected = False
                
        # Fallback to local file storage
        return self._publish_fallback(actual_routing_key, message)

    async def publish_async(self, exchange_or_queue: str, body_or_routing: Any, body: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Publish message asynchronously."""
        if body is not None:
            exchange = exchange_or_queue
            routing_key = body_or_routing
            message = body
        else:
            exchange = ""
            routing_key = exchange_or_queue
            message = body_or_routing
            
        if not self.enable or not self.async_channel or not self.async_connected:
            self._publish_fallback(routing_key, message)
            return {"status": "disabled_or_fallback"}
            
        try:
            msg_str = json.dumps(message, default=str)
            self.async_channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=msg_str,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
            return {"status": "published"}
        except Exception as e:
            self.logger.error(f"❌ Async publish failed: {e}")
            self._publish_fallback(routing_key, message)
            return {"status": "fallback"}

    def _publish_fallback(self, queue_name: str, message: Dict[str, Any]) -> bool:
        try:
            queue_dir = os.path.join(self.fallback_dir, queue_name)
            os.makedirs(queue_dir, exist_ok=True)
            task_id = message.get('task_id', 'unknown')
            file_path = os.path.join(queue_dir, f"{task_id}_{datetime.now().timestamp()}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(message, f, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"❌ Fallback publish failed: {e}")
            return False

    def consume(self, queue_name: str, callback: Callable) -> None:
        """SYNCHRONOUS consume with local fallback loop if disconnected"""
        if not self.connected or not self.channel:
            # Block and poll fallback queue synchronously
            self.logger.info(f"🎧 Consuming from {queue_name} (fallback file queue mode)...")
            try:
                while True:
                    queue_dir = os.path.join(self.fallback_dir, queue_name)
                    if os.path.exists(queue_dir):
                        for file_name in sorted(os.listdir(queue_dir)):
                            if file_name.endswith(".json"):
                                file_path = os.path.join(queue_dir, file_name)
                                try:
                                    with open(file_path, "r", encoding="utf-8") as f:
                                        body = f.read()
                                    class MockMethod:
                                        def __init__(self, delivery_tag):
                                            self.delivery_tag = delivery_tag
                                    class MockCh:
                                        def basic_ack(self, delivery_tag):
                                            try: os.remove(file_path)
                                            except: pass
                                        def basic_nack(self, delivery_tag, requeue=True):
                                            pass
                                    callback(MockCh(), MockMethod(file_name), None, body)
                                except Exception as e:
                                    self.logger.error(f"❌ Error in fallback consume callback: {e}")
                    time.sleep(1.0)
            except KeyboardInterrupt:
                self.logger.info("🎧 Synchronous consume loop interrupted")
            return

        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback)
            self.logger.info(f"🎧 Consuming from {queue_name}...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        finally:
            self.close()

    async def consume_async(self, queue_name: str, callback: Callable) -> None:
        """ASYNCHRONOUS consume with fallback polling"""
        if not self.async_connected or not self.async_channel:
            self.logger.info(f"🎧 Consuming from {queue_name} asynchronously (fallback file queue mode)...")
            while True:
                try:
                    queue_dir = os.path.join(self.fallback_dir, queue_name)
                    if os.path.exists(queue_dir):
                        for file_name in sorted(os.listdir(queue_dir)):
                            if file_name.endswith(".json"):
                                file_path = os.path.join(queue_dir, file_name)
                                try:
                                    with open(file_path, "r", encoding="utf-8") as f:
                                        body = f.read()
                                    class MockMethod:
                                        def __init__(self, delivery_tag):
                                            self.delivery_tag = delivery_tag
                                    class MockCh:
                                        def basic_ack(self, delivery_tag):
                                            try: os.remove(file_path)
                                            except: pass
                                        def basic_nack(self, delivery_tag, requeue=True):
                                            pass
                                    callback(MockCh(), MockMethod(file_name), None, body)
                                except Exception as e:
                                    self.logger.error(f"❌ Error in fallback consume callback: {e}")
                    await asyncio.sleep(1.0)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in fallback consume loop: {e}")
                    await asyncio.sleep(2.0)
            return

        try:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            
            def on_declare(frame):
                self.async_channel.basic_consume(queue=queue_name, on_message_callback=callback)
                self.logger.info(f"🎧 Consuming from {queue_name} asynchronously...")
                
            self.async_channel.queue_declare(queue=queue_name, durable=True, callback=on_declare)
            await future
        except asyncio.CancelledError:
            self.logger.info("🎧 Async consume stopped")
        except Exception as e:
            self.logger.error(f"❌ Async consume error: {e}")

    def setup_dlq(self, queue_name: str) -> bool:
        """Setup a dead letter queue synchronous"""
        if not self.connected or not self.channel: return False
        try:
            dlq_name = f"{queue_name}.dlq"
            self.channel.queue_declare(queue=queue_name, durable=True, arguments={
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': dlq_name
            })
            self.channel.queue_declare(queue=dlq_name, durable=True)
            return True
        except Exception as e:
            self.logger.error(f"❌ DLQ setup failed for queue '{queue_name}': {e}")
            return False

    async def setup_dlq_async(self, queue_name: str) -> bool:
        """Setup a dead letter queue asynchronous"""
        if not self.async_connected or not self.async_channel: return False
        try:
            dlq_name = f"{queue_name}.dlq"
            loop = asyncio.get_running_loop()
            future1 = loop.create_future()
            future2 = loop.create_future()
            
            def on_declare1(frame):
                if not future1.done(): future1.set_result(True)
            def on_declare2(frame):
                if not future2.done(): future2.set_result(True)
                
            self.async_channel.queue_declare(
                queue=queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': dlq_name
                },
                callback=on_declare1
            )
            await asyncio.wait_for(future1, timeout=5.0)
            
            self.async_channel.queue_declare(
                queue=dlq_name,
                durable=True,
                callback=on_declare2
            )
            await asyncio.wait_for(future2, timeout=5.0)
            return True
        except Exception as e:
            self.logger.error(f"❌ Async DLQ setup failed: {e}")
            return False

    def close(self):
        try:
            if self.connection: self.connection.close()
            self.connected = False
        except: pass
        
    async def close_async(self):
        try:
            if self.async_connection:
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                def on_closed(connection, reason):
                    if not future.done(): future.set_result(True)
                self.async_connection.add_on_close_callback(on_closed)
                self.async_connection.close()
                await asyncio.wait_for(future, timeout=5.0)
            self.async_connected = False
        except: pass
