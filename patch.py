import os
import re

class PrecisionPatcher:
    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Файл не найден: {self.file_path}")
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def replace_block(self, target_pattern, replacement, preserve_indent=True):
        """
        Точечно заменяет target_pattern на replacement.
        Проверяет табуляцию/отступы и не затрагивает другие методы.
        """
        # Поиск целевого фрагмента
        match = re.search(target_pattern, self.content, re.MULTILINE)
        if not match:
            raise ValueError(f"Целевой фрагмент не найден в {self.file_path}:\n{target_pattern}")

        start, end = match.span()

        # Определение базового отступа первой строки целевого блока
        line_start = self.content.rfind('\n', 0, start) + 1
        indent_str = self.content[line_start:start]

        # Контроль отступов: запрет смешивания табов и пробелов
        if '\t' in indent_str and ' ' in indent_str:
            raise ValueError(f"ОШИБКА: Обнаружено смешивание табов и пробелов в файле {self.file_path}")

        # Приведение отступов replacement к эталонному уровню блока
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

        # Точечная замена
        self.content = self.content[:start] + formatted_replacement + self.content[end:]

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
        print(f"SUCCESS (Precision In-Place Patch): {self.file_path}")


# ==============================================================================
# ПРИМЕР ТОЧЕЧНОЙ ЗАМЕНЫ (Заменяется строго целевой метод, остальные не трогаются)
# ==============================================================================

print("=== ЗАПУСК ТОЧЕЧНОГО ПАТЧИНГА AUTOTAP ===")

try:
    # Пример: Точечное обновление метода show() в ControlPanelOverlay.kt
    control_panel_path = "app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt"
    if os.path.exists(control_panel_path):
        patcher = PrecisionPatcher(control_panel_path)
        
        # Заменяем точечно только один логический фрагмент (например, лог внутри создания)
        target_code = r"logDiagnostic\(\"OVERLAY\", \"Кнопка btnPlay нажата\.\"\)"
        new_code = 'logDiagnostic("OVERLAY", "Кнопка btnPlay нажата (Precision Patch v37).")'
        
        patcher.replace_block(target_code, new_code)
        patcher.apply()

    print("=== ТОЧЕЧНЫЙ ПАТЧИНГ УСПЕШНО ВЫПОЛНЕН ===")

except Exception as e:
    print(f"ОШИБКА ПАТЧИНГА: {e}")
    sys.exit(1)