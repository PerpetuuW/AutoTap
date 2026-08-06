import os
import sys

def validate_xml(content, filename):
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Ошибка синтаксиса XML в {filename}: {e}")

files = {}

# 1. accessibility_service_config.xml — Добавление разрешения canTakeScreenshot="true"
files["app/src/main/res/xml/accessibility_service_config.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeAllMask"
    android:accessibilityFeedbackType="feedbackGeneric"
    android:accessibilityFlags="flagDefault|flagIncludeNotImportantViews|flagRequestTouchExplorationMode|flagReportViewIds|flagRetrieveInteractiveWindows"
    android:canPerformGestures="true"
    android:canRetrieveWindowContent="true"
    android:canTakeScreenshot="true"
    android:description="@string/accessibility_service_description" />
"""

print("=== ВНЕДРЕНИЕ РАЗРЕШЕНИЯ canTakeScreenshot В ACCESSIBILITY CONFIG ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    validate_xml(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== РАЗРЕШЕНИЕ УСПЕШНО ДОБАВЛЕНО ===")