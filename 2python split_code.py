#!/usr/bin/env python3
import os
import sys

CHUNK_SIZE = 800
OUTPUT_DIR = "kt_chunks_output"

def sanitize_filename(path: str) -> str:
    """
    Превращает путь вида:
        app/src/main/java/com/example/autotap/MyAutoClickService.kt
    в:
        app_src_main_java_com_example_autotap_MyAutoClickService.kt
    чтобы не создавать вложенные папки.
    """
    return path.replace(os.sep, "_")

def split_and_index_file(file_path, rel_path):
    """
    Разбивает один .kt файл на части по CHUNK_SIZE строк
    с сохранением отступов и добавлением глубины [D:x].
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)
    if total_lines == 0:
        print(f"[!] Пустой файл: {file_path}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_parts = (total_lines + CHUNK_SIZE - 1) // CHUNK_SIZE
    current_depth = 0

    safe_name = sanitize_filename(rel_path)

    for part_idx in range(1, total_parts + 1):
        start_line = (part_idx - 1) * CHUNK_SIZE
        end_line = min(part_idx * CHUNK_SIZE, total_lines)

        chunk_lines = []
        part_start_depth = current_depth

        for idx in range(start_line, end_line):
            raw_line = lines[idx]
            clean_line = raw_line.rstrip("\r\n")

            opens = raw_line.count("{")
            closes = raw_line.count("}")

            stripped = raw_line.lstrip()
            display_depth = current_depth
            if stripped.startswith("}"):
                display_depth = max(0, current_depth - 1)

            formatted = f"{idx + 1:4d} | [D:{display_depth}] | {clean_line}"
            chunk_lines.append(formatted)

            current_depth += (opens - closes)
            if current_depth < 0:
                current_depth = 0

        chunk_filename = f"{safe_name}_part_{part_idx:02d}_lines_{start_line+1:04d}_to_{end_line:04d}.txt"
        chunk_path = os.path.join(OUTPUT_DIR, chunk_filename)

        header = (
            f"================================================================================\n"
            f" FILE: {rel_path}\n"
            f" PART: {part_idx}/{total_parts} | LINES: {start_line+1}..{end_line}\n"
            f" START DEPTH: [D:{part_start_depth}] | END DEPTH: [D:{current_depth}]\n"
            f"================================================================================\n\n"
        )
        footer = (
            f"\n\n================================================================================\n"
            f" END OF FILE PART: {chunk_filename}\n"
            f"================================================================================\n"
        )

        with open(chunk_path, "w", encoding="utf-8") as out:
            out.write(header)
            out.write("\n".join(chunk_lines))
            out.write(footer)

        print(f"[+] {chunk_path} (строки {start_line+1}..{end_line})")


def find_all_kt_files(root_dir):
    """
    Ищет все .kt файлы в проекте.
    """
    kt_files = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".kt"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, root_dir)
                kt_files.append((full_path, rel_path))
    return kt_files


if __name__ == "__main__":
    project_root = os.getcwd()
    print(f"[i] Поиск .kt файлов в проекте: {project_root}")

    kt_files = find_all_kt_files(project_root)
    print(f"[i] Найдено .kt файлов: {len(kt_files)}")

    if not kt_files:
        print("[!] Нет .kt файлов.")
        sys.exit(0)

    for full_path, rel_path in kt_files:
        print(f"\n=== Обработка файла: {rel_path} ===")
        split_and_index_file(full_path, rel_path)

    print(f"\n[✓] Все файлы обработаны. Результат в папке '{OUTPUT_DIR}'.")