import os
import re

PATTERNS = [
    r'threading\.Thread', r'asyncio\.create_task', r'subprocess\.run',
    r'subprocess\.Popen', r'os\.system', r'shell=True', r'git push',
    r'git commit', r'uvicorn\.run', r'pika\.BlockingConnection',
    r'redis\.Redis', r'httpx\.AsyncClient', r'requests\.',
    r'google\.generativeai', r'genai', r'Whisper', r'faster_whisper',
    r'Ear\(', r'Brain\(', r'QueryEngine\(', r'live_trade', r'withdrawal',
    r'youtube_upload', r'external_publish'
]

def audit_patterns():
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'dist', 'build', 'OLD_GIT_BACKUP', 'scratch', 'site-packages'}
    findings = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not any(x in d or x in root for x in exclude_dirs)]
        for f in files:
            if not f.endswith(('.py', '.yaml', '.yml', '.md')): continue
            path = os.path.join(root, f)
            if 'OLD_GIT_BACKUP' in path or 'scratch' in path: continue
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    for i, line in enumerate(file, 1):
                        for p in PATTERNS:
                            if re.search(p, line):
                                findings.append((path, i, p, line.strip()[:100]))
            except Exception:
                pass
                
    with open('runtime_audit_output.txt', 'w', encoding='utf-8') as out:
        out.write("Runtime Side-Effects found:\n")
        for path, line, p, text in findings:
            out.write(f"{path}:{line} -> {p} ({text})\n")
    print(f"Audit complete. Found {len(findings)} patterns. Check runtime_audit_output.txt")

if __name__ == '__main__':
    audit_patterns()
