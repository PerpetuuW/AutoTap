import os
import zipfile
from datetime import datetime
from pathlib import Path

# Папки, которые ИСКЛЮЧАЮТСЯ из архива (скомпилированный мусор и кэши)
EXCLUDE_DIRS = {
    '.gradle',
    '.idea',
    'build',
    'app/build',
    '.git',
    '.venv',
    '__pycache__',
    'captures',
    '.vs'
}

# Расширения файлов, которые ИСКЛЮЧАЮТСЯ из архива
EXCLUDE_EXTS = {
    '.apk', '.aab', '.zip', '.tar', '.gz', '.rar', '.7z',
    '.class', '.pyc', '.log', '.tmp', '.bak'
}

def create_project_backup():
    project_root = Path.cwd()
    project_name = project_root.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{project_name}_src_{timestamp}.zip"
    
    print(f"📦 Упаковка проекта '{project_name}'...")
    print(f"📂 Корневая директория: {project_root}\n")

    files_count = 0
    total_size = 0

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_root):
            rel_root = Path(root).relative_to(project_root)
            
            # Пропускаем исключенные директории
            dirs[:] = [
                d for d in dirs 
                if str(rel_root / d).replace('\\', '/') not in EXCLUDE_DIRS 
                and d not in EXCLUDE_DIRS
            ]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(project_root)
                rel_str = str(rel_path).replace('\\', '/')

                # Пропускаем сам создаваемый архив и файлы с исключенными расширениями
                if file == output_filename or file_path.suffix.lower() in EXCLUDE_EXTS:
                    continue

                # Добавляем нужный файл в архив
                zipf.write(file_path, arcname=rel_str)
                files_count += 1
                total_size += file_path.stat().st_size
                print(f"  [+] {rel_str}")

    zip_size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    orig_size_mb = total_size / (1024 * 1024)

    print("\n" + "=" * 50)
    print(f"🎉 Успешно создано: {output_filename}")
    print(f"📄 Упаковано файлов: {files_count}")
    print(f"📊 Исходный размер исходников: {orig_size_mb:.2f} МБ")
    print(f"🗜 Размер ZIP-архива: {zip_size_mb:.2f} МБ")
    print("=" * 50)

if __name__ == "__main__":
    create_project_backup()