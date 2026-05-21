import os
import re

def audit_env():
    env_vars = set()
    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'node_modules' in root or '.venv' in root: continue
        for f in files:
            if not f.endswith('.py'): continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = re.findall(r'os\.environ\.get\([\'"]([A-Z0-9_]+)[\'"]', content)
                    matches += re.findall(r'os\.getenv\([\'"]([A-Z0-9_]+)[\'"]', content)
                    for m in matches: env_vars.add(m)
            except: pass
            
    print("Found ENV variables in code:")
    for e in env_vars:
        print(e)
        
if __name__ == '__main__':
    audit_env()
