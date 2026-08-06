import os
import re
import sys

class PrecisionPatcher:
    """
    Движок точечного патчинга: заменяет строго целевой фрагмент кода,
    не затрагивая и не срезая другие методы в файле.
    """
    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Файл не найден: {self.file_path}")
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def replace_block(self, target_pattern, replacement, preserve_indent=True):
        match = re.search(target_pattern, self.content, re.MULTILINE)
        if not match:
            print(f"⚠️ ВНИМАНИЕ: Целевой фрагмент не найден в {os.path.basename(self.file_path)}, замена пропущена.")
            return False

        start, end = match.span()

        # Считывание уровня отступа целевой строки
        line_start = self.content.rfind('\n', 0, start) + 1
        indent_str = self.content[line_start:start]

        if '\t' in indent_str and ' ' in indent_str:
            raise ValueError(f"ОШИБКА: Обнаружено смешивание табов и пробелов в отступе {self.file_path}")

        # Выравнивание отступов replacement под стиль файла
        if preserve_indent and indent_str.strip() == '':
            lines = replacement.strip('\n').split('\n')
            formatted_lines = []
            for i, line in enumerate(lines):
                if i == 0 or line.strip() == '':
                    formatted_lines.append(line.strip('\r'))
                else:
                    formatted_lines.append(indent_str + line.strip('\r').lstrip())
            formatted_replacement = '\n'.join(formatted_lines)
        else:
            formatted_replacement = replacement.strip('\r')

        # Точечная замена фрагмента (остальной код не затрагивается!)
        self.content = self.content[:start] + formatted_replacement + self.content[end:]
        return True

    def validate_brackets(self):
        brackets = {'(': ')', '{': '}', '[': ']'}
        stack = []
        for char in self.content:
            if char in brackets.keys():
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    raise ValueError(f"Ошибка скобок в {self.file_path}: Лишняя закрывающая скобка '{char}'")
                top = stack.pop()
                if brackets[top] != char:
                    raise ValueError(f"Ошибка скобок в {self.file_path}: Несоответствие скобок '{top}' и '{char}'")
        if stack:
            raise ValueError(f"Ошибка скобок в {self.file_path}: Незакрытые скобки {stack}")

    def apply(self):
        self.validate_brackets()
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
        print(f"🟢 SUCCESS (Precision Patch): {os.path.basename(self.file_path)}")


def verify_all_files_completeness():
    print("======================================================================")
    print("       🔎 ПРОВЕРКА ПОЛНОТЫ И ОТСУТСТВИЯ ОБРЕЗАНИЯ ФАЙЛОВ")
    print("======================================================================\n")

    java_dir = os.path.join("app", "src", "main", "java")
    if not os.path.exists(java_dir):
        print(f"🔴 ОШИБКА: Каталог {java_dir} не найден!")
        return

    kt_files = []
    for root, _, files in os.walk(java_dir):
        for f in files:
            if f.endswith('.kt'):
                kt_files.append(os.path.join(root, f))

    short_files = []
    syntax_error_files = []

    for kt_file in kt_files:
        filename = os.path.basename(kt_file)
        with open(kt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            line_count = len(lines)
            content = "".join(lines)

        # Проверка баланса скобок
        try:
            patcher = PrecisionPatcher(kt_file)
            patcher.validate_brackets()
            bracket_status = "🟢 Скобки OK"
        except Exception as e:
            bracket_status = f"🔴 ОШИБКА СКОБОК: {e}"
            syntax_error_files.append((filename, str(e)))

        # Подозрение на обрезание (если файл меньше 15 строк)
        if line_count < 15:
            short_files.append((filename, line_count))
            print(f"  ⚠️  Подозрительно короткий файл: {filename} ({line_count} строк) | {bracket_status}")
        else:
            print(f"  🟢 {filename}: {line_count} строк | {bracket_status}")

    print("\n======================================================================")
    print("                    📊 ИТОГИ ПРОВЕРКИ ПОЛНОТЫ")
    print("======================================================================")
    print(f" • Всего просканировано Kotlin-файлов: {len(kt_files)}")
    print(f" • Ошибок синтаксиса/скобок: {len(syntax_error_files)}")
    print(f" • Коротких файлов (<15 строк): {len(short_files)}")
    print("======================================================================\n")


if __name__ == "__main__":
    verify_all_files_completeness()