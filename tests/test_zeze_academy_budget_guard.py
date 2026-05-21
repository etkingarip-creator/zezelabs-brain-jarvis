import pytest
from core.zeze_academy.budget_guard import BudgetGuard
from core.zeze_academy.storage import get_academy_storage

@pytest.fixture(autouse=True)
def reset_storage():
    get_academy_storage().budgets.clear()
    get_academy_storage().spends.clear()

def test_budget_guard():
    guard = BudgetGuard()
    
    # 7. budget set edilir
    guard.set_budget("t1", 100.0)
    
    # 8. spend kaydı yapılır
    guard.record_spend("t1", 50.0)
    
    # 10. budget aşılmadıysa freeze false
    assert guard.should_freeze_training("t1") is False
    
    # 9. budget aşılınca freeze true
    guard.record_spend("t1", 60.0)
    assert guard.should_freeze_training("t1") is True
    
    # 11. negatif budget reject
    with pytest.raises(ValueError):
        guard.set_budget("t1", -10.0)
        
    # 12. negatif spend reject
    with pytest.raises(ValueError):
        guard.record_spend("t1", -5.0)
