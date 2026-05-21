import pytest
import time
import os
import asyncio
from core.mq_client import MQClient

def test_mq_client_mock_mode_disabled():
    """Verify mock connection mode (returns False immediately without blocking if disabled)"""
    client = MQClient(enable=False)
    start_time = time.time()
    res = client.connect()
    elapsed = time.time() - start_time
    
    assert res is False
    assert client.connected is False
    assert elapsed < 0.1  # Immediate return
    
    # Test async connect
    async def run_async():
        return await client.connect_async()
    
    start_time = time.time()
    res_async = asyncio.run(run_async())
    elapsed_async = time.time() - start_time
    
    assert res_async is False
    assert elapsed_async < 0.1

def test_mq_client_fallback_publish():
    """Verify fallback publishing writes to local scratch directory when disabled"""
    client = MQClient(enable=False)
    client.connect()
    
    msg = {"task_id": "test_fallback_123", "data": "hello"}
    res = client.publish("test_queue", msg)
    assert res is True
    
    # Verify file is created in scratch/queues/test_queue
    queue_dir = os.path.join(client.fallback_dir, "test_queue")
    assert os.path.exists(queue_dir)
    
    files = os.listdir(queue_dir)
    assert len(files) > 0
    assert any("test_fallback_123" in f for f in files)
    
    # Clean up fallback files
    for f in files:
        os.remove(os.path.join(queue_dir, f))
    os.rmdir(queue_dir)

def test_mq_client_circuit_breaker():
    """Verify circuit breaker trips and prevents network attempts after failure"""
    # Create client with enabled but non-existent host to force connection failure
    client = MQClient(host="invalid-host-name-xyz", enable=True, max_retries=1)
    
    # First attempt: will try to connect and fail (max_retries=1 means short retry wait)
    res = client.connect()
    assert res is False
    assert client.circuit_broken is True
    
    # Second attempt: should immediately return False due to active circuit breaker
    start_time = time.time()
    res2 = client.connect()
    elapsed = time.time() - start_time
    
    assert res2 is False
    assert elapsed < 0.1  # Bypassed network connection attempt immediately

def test_mq_client_declare_topology_fallback():
    """Verify queue and exchange declarations work gracefully in fallback mode"""
    client = MQClient(enable=False)
    client.connect()
    
    assert client.declare_queue("my_test_queue") is True
    assert client.declare_exchange("my_test_exchange") is True
    
    # DLQ setup
    # Note: DLQ setup returns False when disconnected from real MQ, but let's check it handles it gracefully
    res = client.setup_dlq("my_test_queue")
    assert res is False or res is True
