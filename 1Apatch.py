import os

print("=== ДЕРЕВО ПРОЕКТА AUTOTAP (ВЕТКА 13) ===")
root_dir = "app/src/main"

for root, dirs, files in os.walk(root_dir):
    level = root.replace(root_dir, '').count(os.sep)
    indent = ' ' * 4 * (level)
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        if f.endswith(('.kt', '.xml', '.gradle', '.kts')):
            print(f"{subindent}{f}")