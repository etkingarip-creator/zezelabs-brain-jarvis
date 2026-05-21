from core.zeze_academy.storage import get_academy_storage
from core.zeze_academy.tenant_policy import TenantPolicy

class BudgetGuard:
    def __init__(self):
        self.storage = get_academy_storage()
        self.policy = TenantPolicy()

    def set_budget(self, tenant_id: str, monthly_usd: float):
        self.policy.assert_tenant_id(tenant_id)
        if monthly_usd < 0:
            raise ValueError("Budget cannot be negative")
        self.storage.budgets[tenant_id] = monthly_usd

    def record_spend(self, tenant_id: str, amount_usd: float):
        self.policy.assert_tenant_id(tenant_id)
        if amount_usd < 0:
            raise ValueError("Spend cannot be negative")
        current = self.storage.spends.get(tenant_id, 0.0)
        self.storage.spends[tenant_id] = current + amount_usd

    def get_spend(self, tenant_id: str) -> float:
        self.policy.assert_tenant_id(tenant_id)
        return self.storage.spends.get(tenant_id, 0.0)

    def should_freeze_training(self, tenant_id: str) -> bool:
        self.policy.assert_tenant_id(tenant_id)
        budget = self.storage.budgets.get(tenant_id, 0.0)
        spend = self.storage.spends.get(tenant_id, 0.0)
        return spend >= budget if budget > 0 else True
