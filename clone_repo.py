import os
import git

repo_url = "https://github.com/pablodelucca/pixel-agents.git"
target_dir = os.path.join(os.path.dirname(__file__), "pixel_agents_repo")

if not os.path.exists(target_dir):
    print(f"Cloning {repo_url} into {target_dir}...")
    git.Repo.clone_from(repo_url, target_dir)
    print("Clone complete.")
else:
    print(f"Directory {target_dir} already exists.")
