def test_departments_loaded():
    from core.registry import DEPARTMENTS
    assert "app_factory" in DEPARTMENTS

def test_queues_loaded():
    from core.registry import QUEUES
    assert "zeze_app_factory_queue" in QUEUES

def test_features_defaults():
    from core.registry import FEATURES
    assert FEATURES["ZOM_ENABLE_RABBITMQ"]["default"] is False
