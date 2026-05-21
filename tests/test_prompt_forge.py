import pytest
import asyncio
import os
from unittest.mock import MagicMock

from core.prompt_forge.auditor import FailureAuditor, FailureSignature
from core.prompt_forge.sandbox import LocalSandbox, SimulationStats
from core.prompt_forge.evolution_engine import EvolutionEngine

# 1. Auditor Layer Tests
def test_auditor_detects_path_traversal():
    auditor = FailureAuditor()
    telemetry = {
        "event": "tool_execution",
        "task_id": "task-abc-123",
        "agent_id": "jarvis_hybrid",
        "data": {
            "prompt": "Read ../../../secret.txt",
            "error": "Path traversal denied: attempts to traverse outside workspace",
            "execution_status": "failed"
        }
    }
    sig = asyncio.run(auditor.parse_telemetry(telemetry))
    assert sig is not None
    assert sig.task_id == "task-abc-123"
    assert sig.agent_id == "jarvis_hybrid"
    assert sig.error_type == "path_traversal"
    assert sig.signature == "path_traversal_denied"
    assert "secret.txt" in sig.raw_prompt

def test_auditor_detects_loop(monkeypatch):
    # Mock detect_loop in AntiLoopEngine to return True
    mock_detect = MagicMock(return_value={"loop_detected": True, "repeated_signature": "redundant_file_read"})
    monkeypatch.setattr("core.zeze_guard.anti_loop.AntiLoopEngine.detect_loop", mock_detect)

    auditor = FailureAuditor()
    telemetry = {
        "event": "tool_execution",
        "task_id": "task-loop-789",
        "agent_id": "jarvis_hybrid",
        "data": {
            "prompt": "Keep listing directory files",
            "execution_status": "success"
        }
    }
    
    sig = asyncio.run(auditor.parse_telemetry(telemetry))
    assert sig is not None
    assert sig.task_id == "task-loop-789"
    assert sig.error_type == "loop_detected"
    assert sig.signature == "redundant_file_read"

# 2. Sandbox Layer Tests
def test_sandbox_evaluates_correct_prompt_candidate():
    sandbox = LocalSandbox()
    
    # Define a signature for path traversal
    sig = FailureSignature(
        task_id="test-task",
        agent_id="test-agent",
        error_type="path_traversal",
        signature="path_traversal_denied",
        raw_prompt="Read ../../../secret.txt"
    )
    
    # An uncorrected prompt candidate (no path traversal guardrails mentioned)
    bad_candidate = "You are a helpful assistant. Open files and execute tasks."
    bad_stats = asyncio.run(sandbox.run_simulation(bad_candidate, sig, runs=100))
    
    # A corrected prompt candidate containing path traversal rules
    good_candidate = "You are a helpful assistant. Security rule: never use path traversal outside workspace."
    good_stats = asyncio.run(sandbox.run_simulation(good_candidate, sig, runs=100))
    
    # Good prompt candidate must have a higher success rate
    assert good_stats.success_rate > bad_stats.success_rate
    assert good_stats.successes >= bad_stats.successes
    assert good_stats.runs == 100

# 3. Evolution Engine Tests
def test_evolution_engine_updates_prompt():
    engine = EvolutionEngine()
    
    current_prompt = "You are an autonomous shell coder."
    sig = FailureSignature(
        task_id="task-1",
        agent_id="agent-1",
        error_type="loop_detected",
        signature="infinite_loop_detected",
        raw_prompt="Run compile loop"
    )
    
    stats = SimulationStats(
        runs=100,
        successes=15,
        failures=85,
        success_rate=0.15,
        context_drift=0.1,
        recommendation="PROMPT REJECTED"
    )
    
    # Evolve the prompt (mock evolution should trigger since deepseek is mocked or offline)
    updated_prompt = asyncio.run(engine.evolve_prompt(current_prompt, sig, stats))
    
    assert updated_prompt != current_prompt
    assert "ANTI-LOOP PREVENTATIVE" in updated_prompt
    assert "circular dependency" in updated_prompt.lower()

# 4. E2E Pipeline Integration Test
def test_prompt_forge_e2e_pipeline():
    # 1. Set up 3 layers
    auditor = FailureAuditor()
    sandbox = LocalSandbox()
    engine = EvolutionEngine()
    
    # 2. Simulate raw telemetry payload representing a path traversal failure
    telemetry = {
        "event": "tool_execution",
        "task_id": "e2e-task",
        "agent_id": "jarvis-agent",
        "data": {
            "prompt": "Create a file named ../evil.txt",
            "error": "Path traversal denied",
            "execution_status": "failed"
        }
    }
    
    # Layer 1: Auditor extracts signature
    sig = asyncio.run(auditor.parse_telemetry(telemetry))
    assert sig is not None
    assert sig.error_type == "path_traversal"
    
    # Layer 2: Sandbox runs simulations on candidates
    original_prompt = "You are a file editing assistant."
    
    # Simulate evolution candidate generation
    candidate_prompt = asyncio.run(engine.evolve_prompt(original_prompt, sig, SimulationStats(
        runs=10, successes=1, failures=9, success_rate=0.1
    )))
    
    assert "PATH TRAVERSAL PREVENTATIVE" in candidate_prompt
    
    # Sandbox verifies candidate's performance
    stats = asyncio.run(sandbox.run_simulation(candidate_prompt, sig, runs=50))
    assert stats.success_rate >= 0.80
    assert stats.successes > 40
