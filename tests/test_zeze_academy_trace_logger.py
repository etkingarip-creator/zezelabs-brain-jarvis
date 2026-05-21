import pytest
from core.zeze_academy.trace_logger import TraceLogger
from core.zeze_academy.storage import get_academy_storage

@pytest.fixture(autouse=True)
def reset_storage():
    get_academy_storage().traces.clear()

def test_trace_logger():
    logger = TraceLogger()
    
    # 1. trace kaydı yapılır
    logger.record_trace("t1", "ag1", "task1", "action", True, "sig1")
    assert len(logger.get_traces("t1")) == 1
    
    # 2. tenant_id yoksa reject
    with pytest.raises(ValueError):
        logger.record_trace("", "ag1", "task1", "action", True, "sig1")
        
    # 3. agent_id yoksa reject
    with pytest.raises(ValueError):
        logger.record_trace("t1", "", "task1", "action", True, "sig1")
        
    # 4. task_id yoksa reject
    with pytest.raises(ValueError):
        logger.record_trace("t1", "ag1", "", "action", True, "sig1")
        
    # 5. tenant bazlı export sadece kendi trace'lerini içerir
    logger.record_trace("t2", "ag1", "task2", "action", True, "sig2")
    export = logger.export_jsonl("t1")
    assert "t1" in export
    assert "t2" not in export
    
    # 6. secret redaction exportta çalışır
    logger.record_trace("t1", "ag1", "task3", "action", True, "api_key=123")
    export = logger.export_jsonl("t1")
    assert "api_key=123" not in export
    assert "[REDACTED]" in export
