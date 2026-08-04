import os
import zipfile
from datetime import datetime
from pathlib import Path

# Файлы конфигурации в корне проекта
ROOT_CONFIG_FILES = {
    "build.gradle.kts", "build.gradle",
    "settings.gradle.kts", "settings.gradle",
    "gradle.properties",
    "gradlew", "gradlew.bat"
}

# Файлы конфигурации внутри модуля app/
APP_CONFIG_FILES = {
    "build.gradle.kts", "build.gradle",
    "proguard-rules.pro"
}

# Разрешенные расширения в исходниках и ресурсах (app/src/)
ALLOWED_SRC_EXTENSIONS = {
    ".kt", ".java", ".xml", ".png", ".jpg", ".jpeg", 
    ".webp", ".json", ".properties", ".pro"
}

def export_minimal_project():
    project_root = Path.cwd()
    project_name = project_root.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_zip = f"{project_name}_MINIMAL_{timestamp}.zip"

    print("=" * 60)
    print(f"📦 СБОРКА МИНИМАЛЬНОГО АРХИВА ПРОЕКТА: {project_name}")
    print(f"📂 Директория: {project_root}")
    print("=" * 60 + "\n")

    files_to_pack = []

    # 1. Корневые конфигурационные файлы
    for file_name in ROOT_CONFIG_FILES:
        f_path = project_root / file_name
        if f_path.exists():
            files_to_pack.append(f_path)

    # 2. Файлы Gradle Wrapper (gradle/wrapper/*)
    wrapper_dir = project_root / "gradle" / "wrapper"
    if wrapper_dir.exists():
        for f_path in wrapper_dir.glob("*"):
            if f_path.is_file():
                files_to_pack.append(f_path)

    # 3. Конфигурация модуля app
    app_dir = project_root / "app"
    for file_name in APP_CONFIG_FILES:
        f_path = app_dir / file_name
        if f_path.exists():
            files_to_pack.append(f_path)

    # 4. Все файлы из app/src/ (Код, Ресурсы XML/PNG, Manifest)
    src_dir = app_dir / "src"
    if src_dir.exists():
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                f_path = Path(root) / file
                # Исключаем системные скрытые файлы типа .DS_Store, .tmp
                if f_path.suffix.lower() in ALLOWED_SRC_EXTENSIONS:
                    files_to_pack.append(f_path)

    # Упаковка в ZIP
    packed_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f_path in files_to_pack:
            rel_path = f_path.relative_to(project_root)
            rel_str = str(rel_path).replace('\\', '/')
            
            zipf.write(f_path, arcname=rel_str)
            packed_count += 1
            file_size = f_path.stat().st_size
            total_uncompressed_bytes += file_size
            print(f"  [+] {rel_str:<50} ({file_size / 1024:.1f} KB)")

    compressed_size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    compressed_size_kb = os.path.getsize(output_zip) / 1024
    uncompressed_size_mb = total_uncompressed_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print(f"🎉 МИНИМАЛЬНЫЙ АРХИВ СОЗДАН: {output_zip}")
    print(f"📄 Упаковано чистых файлов: {packed_count}")
    print(f"📊 Общий размер исходников: {uncompressed_size_mb:.2f} МБ")
    print(f"🗜 Итоговый размер ZIP: {compressed_size_kb:.1f} КБ ({compressed_size_mb:.2f} МБ)")
    print("=" * 60)

if __name__ == "__main__":
    export_minimal_project()