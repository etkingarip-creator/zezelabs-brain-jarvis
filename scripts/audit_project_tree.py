import os
import collections

def audit_tree(root_dir):
    exclude_dirs = {
        '.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv',
        'dist', 'build', '.cache', 'media_factory/dogfood_reports',
        'app_factory/todo_saas', 'zeze_eng/dev_workspace', 'Clawde_Code'
    }
    
    total_files = 0
    total_dirs = 0
    all_files = []
    basenames = collections.defaultdict(list)
    py_files = 0
    test_files = 0
    generated_dirs = []
    
    gen_patterns = ['dogfood_reports', 'paper_state', 'todo_saas', 'dev_workspace', 'logs', 'reports', 'cache', 'tmp']

    for root, dirs, files in os.walk(root_dir):
        rel_root = os.path.relpath(root, root_dir).replace('\\', '/')
        if rel_root == '.':
            rel_root = ''
            
        # exclude
        dirs[:] = [d for d in dirs if not any(x in os.path.join(rel_root, d).replace('\\', '/') for x in exclude_dirs)]
        
        for d in dirs:
            total_dirs += 1
            path = os.path.join(rel_root, d).replace('\\', '/')
            if any(p in path for p in gen_patterns):
                generated_dirs.append(path)

        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f).replace('\\', '/')
            if any(x in rel_path for x in exclude_dirs):
                continue
            total_files += 1
            size = os.path.getsize(path)
            all_files.append((size, rel_path))
            basenames[f].append(rel_path)
            if f.endswith('.py'):
                py_files += 1
                if f.startswith('test_'):
                    test_files += 1

    all_files.sort(reverse=True)
    duplicates = {k: v for k, v in basenames.items() if len(v) > 1}
    
    print(f"Total Files: {total_files}")
    print(f"Total Dirs: {total_dirs}")
    print(f"Python Files: {py_files}")
    print(f"Test Files: {test_files}")
    print("\nTop 20 Largest Files:")
    for size, path in all_files[:20]:
        print(f" - {path} ({size} bytes)")
    print("\nDuplicate Basenames (Top 10):")
    for k, v in list(duplicates.items())[:10]:
        print(f" - {k}: {v}")
    print("\nGenerated Dirs:")
    for g in generated_dirs:
        print(f" - {g}")

if __name__ == '__main__':
    audit_tree('.')
