import os
import math

def split_dump_file(input_file="2full_project_dump.txt", output_folder="dump_chunks", lines_per_file=680):
    # Проверка наличия исходного файла
    if not os.path.exists(input_file):
        print(f"🔴 ОШИБКА: Файл '{input_file}' не найден в текущей директории!")
        return

    # Создание папки для частей в корне проекта
    os.makedirs(output_folder, exist_ok=True)

    # Чтение исходного файла
    print(f"📖 Чтение файла '{input_file}'...")
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    total_lines = len(lines)
    if total_lines == 0:
        print("⚠️ ВНИМАНИЕ: Файл пуст!")
        return

    total_parts = math.ceil(total_lines / lines_per_file)
    print(f"📊 Всего строк: {total_lines}")
    print(f"📦 Будет создано частей: {total_parts} (по не более {lines_per_file} строк в каждой)\n")

    # Нарезка и сохранение частей
    for part_num in range(total_parts):
        start_idx = part_num * lines_per_file
        end_idx = min(start_idx + lines_per_file, total_lines)
        chunk_lines = lines[start_idx:end_idx]

        part_filename = f"part_{part_num + 1:03d}.txt"
        part_filepath = os.path.join(output_folder, part_filename)

        with open(part_filepath, 'w', encoding='utf-8') as out_f:
            out_f.writelines(chunk_lines)

        print(f"  🟢 Сохранена {part_filename}: {len(chunk_lines)} строк (строки {start_idx + 1} - {end_idx})")

    print("\n======================================================================")
    print(f"✅ УСПЕШНО! Все {total_parts} частей сохранены в папку: '{os.path.abspath(output_folder)}'")
    print("======================================================================")

if __name__ == "__main__":
    split_dump_file()