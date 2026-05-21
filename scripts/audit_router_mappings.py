import re

def parse_router():
    with open('core/orchestrator/router_agent.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print("Router Agent Content Mappings:")
    lines = content.split('\n')
    for line in lines:
        if 'if any(w in desc for w in [' in line or 'return "' in line:
            print(line.strip())

if __name__ == '__main__':
    parse_router()
