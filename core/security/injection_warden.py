import re

class InjectionWarden:
    ATTACK_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"forget\s+all\s+rules",
        r"system\s+prompt",
        r"new\s+instructions:",
        r"You\s+are\s+a\s+different",
        r"jailbreak",
        r"override\s+system",
        r"DAN\s+mode",
    ]
    
    async def analyze(self, prompt: str) -> dict:
        threats = []
        for pattern in self.ATTACK_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                threats.append(pattern)
        
        if threats:
            return {"safe": False, "threats": threats, "action": "BLOCKED"}
        return {"safe": True, "threats": []}
