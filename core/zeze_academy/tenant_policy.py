import re

class TenantPolicy:
    def validate_tenant_access(self, tenant_id: str, resource_tenant_id: str) -> bool:
        return tenant_id == resource_tenant_id

    def redact_secrets(self, text: str) -> str:
        patterns = [
            r"(?i)(api_key[='\":\s]+)([a-zA-Z0-9_\-]+)",
            r"(?i)(password[='\":\s]+)([a-zA-Z0-9_\-]+)",
            r"(?i)(secret[='\":\s]+)([a-zA-Z0-9_\-]+)",
            r"(?i)(private_key[='\":\s]+)([a-zA-Z0-9_\-]+)"
        ]
        redacted = text
        for p in patterns:
            redacted = re.sub(p, r"\1[REDACTED]", redacted)
        return redacted

    def assert_tenant_id(self, tenant_id: str):
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required")
