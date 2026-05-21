import pytest
from core.zeze_academy.curriculum_engine import CurriculumEngine
from core.zeze_academy.trace_logger import TraceLogger
from core.zeze_academy.storage import get_academy_storage
from core.zeze_academy.educator_agent import EducatorAgent
from core.zeze_academy.distillation_dataset import DistillationDatasetBuilder

@pytest.fixture(autouse=True)
def reset_storage():
    s = get_academy_storage()
    s.traces.clear()
    s.datasets.clear()

def test_curriculum_engine():
    logger = TraceLogger()
    logger.record_trace("t1", "ag1", "task1", "action", False, "sig1")
    logger.record_trace("t1", "ag1", "task2", "action", True, "sig2")
    
    engine = CurriculumEngine()
    
    # 19. failure trace'lerinden lesson plan üretir
    # 20. success trace'leri ayrı sayılır
    failures = engine.analyze_failures("t1")
    assert len(failures) == 1
    assert failures[0]["task_id"] == "task1"
    
    # 21. prompt mutation approval_required true döner
    # 22. direct mutation apply edilmez (recommendation returns dict)
    mut = engine.recommend_prompt_mutation("t1")
    assert mut["approval_required"] is True

def test_distillation_dataset():
    builder = DistillationDatasetBuilder()
    
    # 26. successful output kaydedilir
    builder.add_trace_example("t1", "do this", "ok done")
    
    # 24. dataset tenant izolasyonu yapar
    builder.add_trace_example("t2", "other", "ok")
    
    # 23. JSONL export üretir
    export = builder.export_dataset_jsonl("t1")
    assert "t1" in export
    assert "t2" not in export
    
    # 25. secret içeren prompt redacted olur
    builder.add_trace_example("t1", "api_key=123", "ok")
    export2 = builder.export_dataset_jsonl("t1")
    assert "api_key=123" not in export2
    assert "[REDACTED]" in export2

def test_educator_agent():
    logger = TraceLogger()
    logger.record_trace("t1", "ag1", "task1", "action", False, "sig1")
    
    educator = EducatorAgent()
    
    # 27. nightly review dict döner
    res = educator.run_nightly_review("t1")
    
    # 28. lesson_plan içerir
    assert "lesson_plan" in res
    
    # 29. prompt_mutation içerir
    assert "prompt_mutation" in res
    
    # 30. approval_required true olur
    assert res["approval_required"] is True
