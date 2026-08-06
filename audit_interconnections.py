import os
import re
import xml.etree.ElementTree as ET

def audit_project_interconnections():
    root_dir = "."
    app_main = os.path.join(root_dir, "app", "src", "main")
    java_dir = os.path.join(app_main, "java")
    res_dir = os.path.join(app_main, "res")
    layout_dir = os.path.join(res_dir, "layout")
    drawable_dir = os.path.join(res_dir, "drawable")
    manifest_file = os.path.join(app_main, "AndroidManifest.xml")

    print("======================================================================")
    print("      🔍 ПОЛНЫЙ АУДИТ ВЗАИМОСВЯЗЕЙ ПРОЕКТА AUTOTAP (v37)")
    print("======================================================================\n")

    # -------------------------------------------------------------------------
    # ФАЗА 1: Сканирование всех Kotlin-файлов
    # -------------------------------------------------------------------------
    kt_files = {}
    kt_classes = set()
    for root, _, files in os.walk(java_dir):
        for f in files:
            if f.endswith('.kt'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, java_dir)
                with open(full_path, 'r', encoding='utf-8') as file_obj:
                    content = file_obj.read()
                    kt_files[rel_path] = content
                    
                    # Извлечение имен классов и объектов
                    class_matches = re.findall(r'(?:class|object|interface)\s+([A-Za-z0-9_]+)', content)
                    for cm in class_matches:
                        kt_classes.add(cm)

    print(f"📦 Просканировано Kotlin-файлов: {len(kt_files)}")
    print(f"🏷️  Найдено объявлений классов/объектов: {len(kt_classes)}\n")

    # -------------------------------------------------------------------------
    # ФАЗА 2: Аудит AndroidManifest.xml
    # -------------------------------------------------------------------------
    print("--- [ФАЗА 1: Проверка AndroidManifest.xml] ---")
    if os.path.exists(manifest_file):
        try:
            tree = ET.parse(manifest_file)
            root = tree.getroot()
            manifest_components = []
            
            for elem in root.iter():
                if elem.tag in ['activity', 'service', 'provider', 'receiver']:
                    for attr_k, attr_v in elem.attrib.items():
                        if attr_k.endswith('name'):
                            manifest_components.append((elem.tag, attr_v))

            for tag, comp in manifest_components:
                short_name = comp.split('.')[-1]
                found = any(short_name in c_name for c_name in kt_classes)
                if found:
                    print(f"  🟢 {tag.capitalize()}: {comp} -> Связан с Kotlin объектом")
                else:
                    print(f"  🔴 {tag.capitalize()}: {comp} -> ОШИБКА: Компонент не найден в коде!")
        except Exception as e:
            print(f"  🔴 Ошибка парсинга AndroidManifest.xml: {e}")
    else:
        print("  🔴 AndroidManifest.xml не найден!")
    print()

    # -------------------------------------------------------------------------
    # ФАЗА 3: Аудит XML-макетов (Layouts <-> Kotlin)
    # -------------------------------------------------------------------------
    print("--- [ФАЗА 2: Связи XML-Макетов и ID <-> Kotlin] ---")
    layout_ids = {}
    if os.path.exists(layout_dir):
        for f in os.listdir(layout_dir):
            if f.endswith('.xml'):
                layout_path = os.path.join(layout_dir, f)
                try:
                    tree = ET.parse(layout_path)
                    root = tree.getroot()
                    ids = set()
                    for elem in root.iter():
                        for k, v in elem.attrib.items():
                            if k.endswith('id') and v.startswith('@+id/'):
                                ids.add(v.replace('@+id/', ''))
                    layout_ids[f] = ids
                except Exception as e:
                    print(f"  🔴 Ошибка XML {f}: {e}")

        for layout_name, ids in layout_ids.items():
            layout_no_ext = layout_name.replace('.xml', '')
            
            # Поиск упоминания макета в Kotlin
            bound_kt = [kt_path for kt_path, content in kt_files.items() if f"R.layout.{layout_no_ext}" in content]
            
            if bound_kt:
                print(f"  🟢 Макет {layout_name} -> Надувается в [{', '.join(bound_kt)}]")
            else:
                print(f"  ⚠️  Макет {layout_name} -> Не надувается напрямую через R.layout (проверьте включение)")

            # Проверка связей ID этого макета
            unbound_ids = []
            for id_name in ids:
                referenced = any(
                    id_name in content or f'"{id_name}"' in content or f'R.id.{id_name}' in content 
                    for content in kt_files.values()
                )
                if not referenced:
                    unbound_ids.append(id_name)

            if unbound_ids:
                print(f"     ⚠️ Несвязанные ID в {layout_name}: {unbound_ids}")
            else:
                print(f"     🟢 Все {len(ids)} ID макета {layout_name} привязаны в Kotlin!")
    print()

    # -------------------------------------------------------------------------
    # ФАЗА 4: Аудит Drawables (Графика <-> XML/Kotlin)
    # -------------------------------------------------------------------------
    print("--- [ФАЗА 3: Связи Графики (res/drawable/)] ---")
    if os.path.exists(drawable_dir):
        drawables = [f.split('.')[0] for f in os.listdir(drawable_dir) if not f.startswith('.')]
        all_xml_content = ""
        
        # Сканирование всех layout XML файлов
        for f in os.listdir(layout_dir):
            if f.endswith('.xml'):
                with open(os.path.join(layout_dir, f), 'r', encoding='utf-8') as xml_f:
                    all_xml_content += xml_f.read() + "\n"

        unused_drawables = []
        for drw in drawables:
            in_xml = f"@drawable/{drw}" in all_xml_content
            in_kt = any(f"R.drawable.{drw}" in c or f'"{drw}"' in c for c in kt_files.values())
            if not (in_xml or in_kt):
                unused_drawables.append(drw)

        if unused_drawables:
            print(f"  ⚠️ Графические файлы без прямых ссылок ({len(unused_drawables)}): {unused_drawables[:10]}...")
            print("     (Примечание: Могут использоваться во вложенных стилях themes.xml)")
        else:
            print(f"  🟢 Все {len(drawables)} файлов из res/drawable/ связаны в проекте!")
    print()

    # -------------------------------------------------------------------------
    # ФАЗА 5: Проверка Связности Ядра Модулей (Core Subsystem Matrix)
    # -------------------------------------------------------------------------
    print("--- [ФАЗА 4: Матрица Связности Ядра AutoTap] ---")
    core_components = {
        "MyAutoClickService": ["GestureExecutor", "ScriptExecutor", "RecordingEngine", "TutorialEngine", "OverlayManager", "AiScannerEngine"],
        "ScriptExecutor": ["ActionConfig", "MyAutoClickService", "GestureExecutor", "AiScannerEngine"],
        "AiScannerEngine": ["TemplateMatcher", "MatchCandidate", "AiScanResult"],
        "TemplateMatcher": ["HybridCascadeMatcher", "TemplateRepository", "SearchModes"],
        "OverlayManager": ["ControlPanelOverlay", "JoystickOverlay", "CaptureFrameOverlay", "ScenarioDebuggerOverlay"],
        "MainActivity": ["MyAutoClickService", "StructuredLogger", "ScriptRepository"]
    }

    for comp, dependencies in core_components.items():
        comp_file = next((path for path, content in kt_files.items() if comp in path), None)
        if comp_file:
            content = kt_files[comp_file]
            missing_deps = []
            for dep in dependencies:
                if dep not in content:
                    missing_deps.append(dep)
            
            if missing_deps:
                print(f"  ⚠️  {comp} -> Отсутствует упоминание зависимостей: {missing_deps}")
            else:
                print(f"  🟢 {comp} -> Все {len(dependencies)} ядерных зависимостей завязаны!")
        else:
            print(f"  🔴 ОШИБКА: Ядерный класс {comp} не найден в проекте!")

    print("\n======================================================================")
    print("                    📊 ИТОГОВЫЙ ОТЧЕТ АУДИТА")
    print("======================================================================")
    print(" Скрипт проверки связности успешно выполнен.")
    print(" Все обнаруженные несвязанные элементы могут быть точечно поправлены.")
    print("======================================================================\n")

if __name__ == "__main__":
    audit_project_interconnections()