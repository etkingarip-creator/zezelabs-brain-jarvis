import re

class TokenSanitizer:
    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{20,}",
        r"ghp_[a-zA-Z0-9]{36}",
        r"AKIA[0-9A-Z]{16}",
        r"xox[baprs]-([0-9a-zA-Z]{10,48})",
        r"-----BEGIN\s+[A-Z]+\s+PRIVATE\s+KEY-----",
    ]
    
    async def sanitize(self, text: str) -> dict:
        leaks = []
        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                leaks.append(pattern)
        
        if leaks:
            sanitized = re.sub(r"sk-[a-zA-Z0-9]{20,}", "sk-***REDACTED***", text)
            # Ensure other patterns are redacted/scrubbed if present
            sanitized = re.sub(r"ghp_[a-zA-Z0-9]{36}", "ghp_***REDACTED***", sanitized)
            sanitized = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA***REDACTED***", sanitized)
            sanitized = re.sub(r"xox[baprs]-([0-9a-zA-Z]{10,48})", "xox-***REDACTED***", sanitized)
            return {"safe": False, "leaks": leaks, "sanitized": sanitized}
        return {"safe": True, "leaks": []}
