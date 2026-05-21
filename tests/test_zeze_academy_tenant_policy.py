import pytest
from core.zeze_academy.tenant_policy import TenantPolicy

def test_tenant_policy():
    policy = TenantPolicy()
    
    # 13. aynı tenant access allowed
    assert policy.validate_tenant_access("t1", "t1") is True
    
    # 14. cross-tenant access denied
    assert policy.validate_tenant_access("t1", "t2") is False
    
    # 15. API key redaction
    assert "api_key=[REDACTED]" in policy.redact_secrets("api_key=sk_test_123")
    
    # 16. password redaction
    assert "password=[REDACTED]" in policy.redact_secrets("password=secretpass")
    
    # 17. private key redaction
    assert "private_key=[REDACTED]" in policy.redact_secrets("private_key=ab123")
    
    # 18. empty tenant_id reject
    with pytest.raises(ValueError):
        policy.assert_tenant_id("")
