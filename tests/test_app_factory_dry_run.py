import os
import pytest
from core.operator_runtime.contracts import AgentResult, DepartmentName
from departments.app_factory.agent import AppFactoryAgent

WORKSPACE = os.path.abspath(".")

def agent():
    return AppFactoryAgent(workspace_root=WORKSPACE)

def test_app_factory_agent_init():
    a = agent()
    assert a.department == DepartmentName.APP_FACTORY
    assert a.workspace_root == WORKSPACE

def test_app_factory_dry_run_success():
    a = agent()
    goal = "basit bir todo saas scaffold oluştur"
    result = a.run_dry_task(goal)
    
    assert isinstance(result, AgentResult)
    assert result.success is True
    assert result.task_id is not None
    assert result.department == DepartmentName.APP_FACTORY
    assert len(result.tool_results) == 4  # README, manifest, main.py, test_smoke.py
    
    # Check if files exist in the workspace
    scaffold_dir = os.path.join(WORKSPACE, "app_factory", "todo_saas")
    assert os.path.exists(os.path.join(scaffold_dir, "README.md"))
    assert os.path.exists(os.path.join(scaffold_dir, "manifest.json"))
    assert os.path.exists(os.path.join(scaffold_dir, "app", "main.py"))
    assert os.path.exists(os.path.join(scaffold_dir, "tests", "test_smoke.py"))

def test_app_factory_idempotent():
    a = agent()
    goal = "basit bir todo saas scaffold oluştur"
    result1 = a.run_dry_task(goal)
    result2 = a.run_dry_task(goal)
    
    assert result1.success is True
    assert result2.success is True
    assert len(result1.tool_results) == 4
    assert len(result2.tool_results) == 4

def test_app_factory_telemetry():
    from core.operator_runtime.telemetry import get_telemetry
    
    tel = get_telemetry()
    before = len(tel.get_events())
    
    a = agent()
    a.run_dry_task("test telemetry")
    
    assert len(tel.get_events()) > before
    
    # Find our event
    events = tel.get_events()
    our_event = next(e for e in reversed(events) if e["tool_name"] == "app_factory_dry_run")
    assert our_event["department"] == DepartmentName.APP_FACTORY
    assert our_event["status"] == "success"
