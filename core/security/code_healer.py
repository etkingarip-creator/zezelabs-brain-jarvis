import re

class CodeHealer:
    VULN_PATTERNS = [
        r"os\.system\s*\(",
        r"subprocess\s*\.\s*(?:run|Popen|call|check_output|check_call)\s*\(",
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"os\.popen\s*\(",
        r"socket\.connect\s*\(",
    ]
    
    async def analyze(self, code: str) -> dict:
        vulns = []
        for pattern in self.VULN_PATTERNS:
            if re.search(pattern, code):
                vulns.append(pattern)
        
        if vulns:
            return {
                "safe": False, 
                "vulnerabilities": vulns, 
                "patched_code": await self.patch(code)
            }
        return {"safe": True, "vulnerabilities": []}
    
    async def patch(self, code: str) -> str:
        # Standard auto-patch mapping os.system to a blocked comment
        patched = code
        patched = patched.replace("os.system", "# BLOCKED os.system")
        patched = patched.replace("eval", "# BLOCKED eval")
        patched = patched.replace("exec", "# BLOCKED exec")
        patched = patched.replace("subprocess", "# BLOCKED subprocess")
        return patched
