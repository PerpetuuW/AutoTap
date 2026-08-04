import os
import zipfile

def is_minimal_project_file(rel_path: str) -> bool:
    """Определяет, входит ли файл в минимально необходимый комплект для переноса Android-проекта."""
    norm_path = rel_path.replace("\\", "/").lower()

    # Игнорируемые временные директории и расширения
    ignore_prefixes = (
        "build/", "app/build/", ".gradle/", ".idea/", ".git/",
        "out/", "captures/", ".autotap_patch_backup/"
    )
    if any(norm_path.startswith(prefix) or f"/{prefix}" in norm_path for prefix in ignore_prefixes):
        return False

    ignore_extensions = (".apk", ".aar", ".zip", ".pyc", ".class", ".log", ".tmp", ".ds_store")
    if norm_path.endswith(ignore_extensions):
        return False

    # Разрешенные корневые конфигурационные файлы Gradle
    allowed_root_files = {
        "build.gradle.kts", "build.gradle",
        "settings.gradle.kts", "settings.gradle",
        "gradle.properties", "gradlew", "gradlew.bat"
    }
    if "/" not in norm_path and norm_path in allowed_root_files:
        return True

    # Разрешенные директории и специфичные файлы модуля
    if norm_path.startswith("gradle/wrapper/"):
        return True

    if norm_path in {"app/build.gradle.kts", "app/build.gradle", "app/proguard-rules.pro"}:
        return True

    if norm_path.startswith("app/src/main/"):
        return True

    return False

def pack_minimal_project(project_root: str, output_zip_name: str = "autotap_minimal_project.zip") -> str:
    """Упаковывает отфильтрованные файлы проекта в ZIP-архив."""
    output_zip_path = os.path.join(project_root, output_zip_name)
    packed_count = 0
    total_bytes = 0

    print(f"[INFO] Сканирование директории проекта: {project_root}")

    with zipfile.ZipFile(output_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(project_root):
            for file in files:
                abs_filepath = os.path.join(root, file)
                rel_filepath = os.path.relpath(abs_filepath, project_root)

                if is_minimal_project_file(rel_filepath):
                    zipf.write(abs_filepath, arcname=rel_filepath)
                    file_size = os.path.getsize(abs_filepath)
                    total_bytes += file_size
                    packed_count += 1
                    print(f"[OK] Упакован: {rel_filepath} ({file_size} байт)")
                else:
                    print(f"[SKIP] Пропущен: {rel_filepath}")

    print(f"[CREATED] Архив успешно сформирован: {output_zip_path}")
    print(f"[INFO] Итого упаковано файлов: {packed_count}, общий исходный размер: {total_bytes / 1024:.2f} КБ")
    return output_zip_path

def main() -> None:
    print("[INFO] Старт сборки минимального комплекта переноса проекта...")
    project_root = os.getcwd()
    archive_path = pack_minimal_project(project_root)
    print(f"[OK] Проект готов к переносу! Архив доступен по пути: {archive_path}")

if __name__ == "__main__":
    main()