import os
import subprocess
import time
import sys
import random
import shlex

def run(cmd):
    print(f"Executing: {cmd}")
    return subprocess.run(shlex.split(cmd), shell=False, capture_output=True, text=True)

def main():
    print("======================================================")
    print("   ZEZELABS GITHUB PUSH ORCHESTRATOR v5.0 (ARCHITECT)")
    print("======================================================")

    # 0. BYPASS & ISOLATE
    print("[0/5] Isolating old history...")
    forbidden_folder = "OLD_GIT_BACKUP_DO_NOT_PUSH"
    if os.path.exists(".git"):
        try:
            if os.path.exists(forbidden_folder):
                forbidden_folder = f"{forbidden_folder}_{random.randint(100, 999)}"
            os.rename(".git", forbidden_folder)
            print(f"✅ Old history isolated in {forbidden_folder}")
        except Exception as e:
            print(f"⚠️ Lock bypass: {e}")

    # 1. Create STRICTEST .gitignore
    print("[1/5] Creating ultimate .gitignore...")
    gitignore_content = f"""
node_modules/
dist/
.env
*.log
__pycache__/
.DS_Store
standalone_jarvis/frontend/node_modules/
frontend/node_modules/
backend/venv/
backend/__pycache__/
*.exe
.git_trash_*
OLD_GIT_BACKUP_*
{forbidden_folder}/
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)

    # 2. Re-initialize
    print("[2/5] Initializing Clean Start...")
    run("git init")
    run("git branch -M main")
    
    # 3. Add & Commit
    print("[3/5] Staging ONLY code files...")
    run("git add .")
    run('git commit -m "Final Clean Integration - Zezelabs Jarvis Unified"')
    
    # 4. Remote
    print("[4/5] Configuring remote...")
    repo_url = "https://github.com/etkingarip-creator/zezelabs-brain-jarvis.git"
    run("git remote remove origin")
    run(f"git remote add origin {repo_url}")
    
    # 5. Push
    print("[5/5] Pushing code...")
    res = subprocess.run(["git", "push", "-u", "origin", "main"], shell=False, timeout=120)
    
    if res.returncode == 0:
        print("\n✅ TOTAL VICTORY! Your system is now LIVE on GitHub.")
        print(f"URL: {repo_url}")
    else:
        print("\n❌ PUSH FAILED!")
        print("Please check your internet or GitHub login.")
    print("======================================================")

if __name__ == "__main__":
    main()
