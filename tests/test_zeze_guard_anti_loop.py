import pytest
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.storage import get_storage

@pytest.fixture(autouse=True)
def reset_storage():
    get_storage().clear()
    yield

def test_same_signature_once_not_loop():
    engine = AntiLoopEngine()
    engine.record_event("agent_1", "task_1", "shell_error", "ls_error_123")
    res = engine.detect_loop("agent_1", "task_1")
    assert res["loop_detected"] is False

def test_same_signature_twice_not_loop():
    engine = AntiLoopEngine()
    engine.record_event("agent_1", "task_1", "shell_error", "ls_error_123")
    engine.record_event("agent_1", "task_1", "shell_error", "ls_error_123")
    res = engine.detect_loop("agent_1", "task_1")
    assert res["loop_detected"] is False

def test_same_signature_thrice_is_loop():
    engine = AntiLoopEngine()
    for _ in range(3):
        engine.record_event("agent_1", "task_1", "shell_error", "ls_error_123")
    res = engine.detect_loop("agent_1", "task_1")
    assert res["loop_detected"] is True
    assert res["repeated_signature"] == "ls_error_123"

def test_should_freeze_queue():
    engine = AntiLoopEngine()
    for _ in range(3):
        engine.record_event("agent_2", "task_2", "file_edit", "patch_fail_456")
    assert engine.should_freeze_queue("agent_2", "task_2") is True

def test_reset_task_clears_loop_state():
    engine = AntiLoopEngine()
    for _ in range(3):
        engine.record_event("agent_2", "task_2", "file_edit", "patch_fail_456")
    assert engine.should_freeze_queue("agent_2", "task_2") is True
    
    engine.reset_task("task_2")
    assert engine.should_freeze_queue("agent_2", "task_2") is False
