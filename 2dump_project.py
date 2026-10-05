import os

# Имя итогового файла
output_filename = "2full_project_dump.txt"

# Расширения исходного кода, которые нужно собрать
allowed_extensions = {".kt", ".java", ".xml", ".gradle", ".kts", ".properties"}

# Папки, которые нужно пропустить (сборка, гиты, кэши)
exclude_dirs = {".git", ".gradle", ".idea", "build", "gradle", "captures", "out", ".externalNativeBuild"}

# Файлы, которые пропускаем
exclude_files = {output_filename, "local.properties"}

def dump_project():
    root_dir = "."
    files_count = 0
    
    print("🚀 Начинаем сборку исходного кода проекта...\n")
    
    with open(output_filename, "w", encoding="utf-8") as out:
        out.write("=== AUTOTAP FULL PROJECT SOURCE DUMP ===\n\n")
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Фильтруем папки
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            
            for filename in filenames:
                if filename in exclude_files:
                    continue
                    
                ext = os.path.splitext(filename)[1].lower()
                if ext in allowed_extensions:
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                    
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        out.write(f"--- START OF FILE: {rel_path} ---\n")
                        out.write(content)
                        out.write(f"\n--- END OF FILE: {rel_path} ---\n\n")
                        
                        files_count += 1
                        print(f"[+] Упакован: {rel_path}")
                    except Exception as e:
                        print(f"[-] Пропущен (ошибка чтения) {rel_path}: {e}")

    print(f"\n[УСПЕШНО] Собрано файлов: {files_count}")
    print(f"[ФАЙЛ ГОТОВ] Весь код сохранен в '{output_filename}'!")

if __name__ == "__main__":
    dump_project()