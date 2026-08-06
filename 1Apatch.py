import os
import sys

def validate_kotlin(content, filename):
    brackets = {'(': ')', '{': '}', '[': ']'}
    stack = []
    for char in content:
        if char in brackets.keys():
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Лишняя закрывающая скобка '{char}'")
            top = stack.pop()
            if brackets[top] != char:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Несоответствие скобок '{top}' и '{char}'")
    if stack:
        raise ValueError(f"Ошибка синтаксиса в {filename}: Незакрытые скобки {stack}")

    forbidden = ["TODO()", "// остальной код", "// TODO"]
    for item in forbidden:
        if item in content:
            raise ValueError(f"Обнаружена запрещенная заглушка '{item}' в файле {filename}")

files = {}

# 1. InfoHelpDialog.kt — Диалог справки по приложению
files["app/src/main/java/com/example/autotap/ui/overlays/InfoHelpDialog.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class InfoHelpDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        width = 900
        height = 1200
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.7f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#EE1E1E2C"))
            setPadding(32, 32, 32, 32)
        }

        val title = TextView(context).apply {
            text = "📖 Руководство и Справка AutoTap v35/v37"
            setTextColor(Color.WHITE)
            textSize = 18f
            setPadding(0, 0, 0, 16)
        }
        root.addView(title)

        val scrollView = ScrollView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        }

        val helpContentText = TextView(context).apply {
            setTextColor(Color.parseColor("#DDDDDD"))
            textSize = 13f
            text = getHelpText()
        }
        scrollView.addView(helpContentText)
        root.addView(scrollView)

        val btnClose = Button(context).apply {
            text = "Понятно"
            setOnClickListener {
                logDiagnostic("UI", "Закрыта справка по работе приложения.")
                hide()
            }
        }
        root.addView(btnClose)

        return root
    }

    private fun getHelpText(): String {
        return \"\"\"
        ⭐ ДОБРО ПОЖАЛОВАТЬ В AUTOTAP (v35/v37)
        Профессиональный комплекс авто-кликов, компьютерного зрения и записи сценариев.

        ══════════════════════════════════════════
        🧠 1. УМНАЯ МАСКА И ИИ-ПОИСК (CalibratedMask)
        • Авто-калибровка: При вырезании шаблона система вычисляет контуры (Sobel), выравнивает контраст (CLAHE) и удаляет фон.
        • Семейства масок (Profiles):
          - SMALL (иконки, крестики) — приоритетный поиск на 1.25x/1.4x.
          - MEDIUM (кнопки, карточки) — базовый поиск 1.0x.
          - LARGE (окна, панели) — ускоренный шаг каскада.
          - THIN_LINE (рамки, полоски HP) — поиск по Собель-градиентам.
        • Ручная калибровка: Кнопка «Калибровка маски» сбрасывает кэш и пересчитывает контуры.

        ══════════════════════════════════════════
        🔄 2. МУЛЬТИПОИСК (Continuous Multi-Search)
        • Поддержка нескольких масок на одном шаге.
        • Реактивный цикл: Захват снимка -> Поиск -> Клик -> Пауза -> СВЕЖИЙ снимок -> Повтор до нажатия СТОП.

        ══════════════════════════════════════════
        🎥 3. ЗАПИСЬ И ВОСПРОИЗВЕДЕНИЕ (Recording Engine)
        • Запись действий поверх оверлеев без перехвата чужих кликов.
        • Сохранение сценариев в формате JSON с нормализованными координатами.

        ══════════════════════════════════════════
        🎮 4. ИНТЕРАКТИВНЫЙ ДЖОЙСТИК (Joystick Control)
        • Движение Knob в 25 FPS с одновременным управлением и записью траектории.
        • Точное повторение recordedJoystickPath при воспроизведении.

        ══════════════════════════════════════════
        🛡️ 5. ЗАЩИТА ОТ САМО-НАЖАТИЙ (Anti-Self-Click)
        • Оверлеи используют FLAG_NOT_TOUCHABLE во время выполнения жестов.
        • Фильтр isOverlayArea() автоматически отменяет жесты, если они попадают в область UI-панелей.

        ══════════════════════════════════════════
        🎓 6. ИНТЕРАКТИВНОЕ ОБУЧЕНИЕ (Tutorial Engine)
        • Подсветка элементов экрана с эффектом PorterDuff.Mode.CLEAR и подсказками.

        ══════════════════════════════════════════
        📋 7. ДИАГНОСТИКА И ЛОГИ (StructuredLogger)
        • Миллисекундные штампы времени.
        • Авто-усечение файла error_log.txt при превышении 512 КБ.
        • Экран просмотра логов c функцией «Поделиться» через FileProvider.
        \"\"\".trimIndent()
    }
}
"""

# 2. Обновленный OverlayManager.kt c добавлением infoHelpDialog
files["app/src/main/java/com/example/autotap/ui/base/OverlayManager.kt"] = """package com.example.autotap.ui.base

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.CandidateSelectionOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ClickVisualizerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.InfoHelpDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.ScriptsDialog
import com.example.autotap.ui.overlays.TutorialOverlay

class OverlayManager(val context: Context) {

    val controlPanel by lazy { ControlPanelOverlay(context, this) }
    val debuggerOverlay by lazy { ScenarioDebuggerOverlay(context, this) }
    val candidateOverlay by lazy { CandidateSelectionOverlay(context, this) }
    val joystickOverlay by lazy { JoystickOverlay(context, this) }
    val editActionDialog by lazy { EditActionDialog(context, this) }
    val captureFrameOverlay by lazy { CaptureFrameOverlay(context, this) }
    val scriptsDialog by lazy { ScriptsDialog(context, this) }
    val clickVisualizer by lazy { ClickVisualizerOverlay(context, this) }
    val tutorialOverlay by lazy { TutorialOverlay(context, this) }
    val infoHelpDialog by lazy { InfoHelpDialog(context, this) }

    fun showControlPanel() {
        controlPanel.show()
    }

    fun hideControlPanel() {
        controlPanel.hide()
    }

    fun showFloatingStopButton() {
        logDiagnostic("OVERLAY", "Отображена плавающая кнопка СТОП.")
    }

    fun hideFloatingStopButton() {
        logDiagnostic("OVERLAY", "Скрыта плавающая кнопка СТОП.")
    }

    fun showClickVisualizer(x: Float, y: Float) {
        clickVisualizer.showClickAt(x, y)
    }

    fun hideAll() {
        controlPanel.hide()
        debuggerOverlay.hide()
        candidateOverlay.hide()
        joystickOverlay.hide()
        editActionDialog.hide()
        captureFrameOverlay.hide()
        scriptsDialog.hide()
        clickVisualizer.hide()
        tutorialOverlay.hide()
        infoHelpDialog.hide()
    }
}
"""

# 3. ControlPanelOverlay.kt — Добавление кнопки «СПРАВКА»
files["app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val container = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#DD1E1E2C"))
            setPadding(24, 24, 24, 24)
        }

        val titleText = TextView(context).apply {
            text = "AutoTap v35 Control"
            setTextColor(Color.WHITE)
            textSize = 16f
            setPadding(0, 0, 0, 16)
        }
        container.addView(titleText)

        val btnStart = Button(context).apply {
            text = "СТАРТ"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка СТАРТ нажата.")
                MyAutoClickService.instance?.scriptExecutor?.start()
            }
        }
        container.addView(btnStart)

        val btnAddAction = Button(context).apply {
            text = "+ ДЕЙСТВИЕ"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка +ДЕЙСТВИЕ нажата.")
                overlayManager.captureFrameOverlay.show()
            }
        }
        container.addView(btnAddAction)

        val btnScripts = Button(context).apply {
            text = "СЦЕНАРИИ"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка СЦЕНАРИИ нажата.")
                overlayManager.scriptsDialog.show()
            }
        }
        container.addView(btnScripts)

        val btnHelp = Button(context).apply {
            text = "СПРАВКА"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Открытие справки InfoHelpDialog.")
                overlayManager.infoHelpDialog.show()
            }
        }
        container.addView(btnHelp)

        val btnStop = Button(context).apply {
            text = "СТОП"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка СТОП нажата.")
                MyAutoClickService.instance?.scriptExecutor?.stop()
                hide()
            }
        }
        container.addView(btnStop)

        setupDragAndDrop(container)
        return container
    }
}
"""

# 4. MainActivity.kt — Добавление кнопки перехода к Справке
files["app/src/main/java/com/example/autotap/MainActivity.kt"] = """package com.example.autotap

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.LogViewerActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        StructuredLogger.init(this)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        val statusText = TextView(this).apply {
            text = "AutoTap v35 System Status"
            textSize = 18f
            setPadding(0, 0, 0, 16)
        }
        layout.addView(statusText)

        val btnAccessibility = Button(this).apply {
            text = "Включить Accessibility Service"
            setOnClickListener {
                try {
                    startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                } catch (e: Exception) {
                    logError("UI", "Ошибка перехода в настройки Accessibility", e)
                }
            }
        }
        layout.addView(btnAccessibility)

        val btnOverlay = Button(this).apply {
            text = "Запустить Overlay Панель"
            setOnClickListener {
                val service = MyAutoClickService.instance
                if (service != null) {
                    service.showControlPanel()
                    logDiagnostic("UI", "Запрос показа Control Panel из MainActivity")
                } else {
                    logError("UI", "MyAutoClickService не запущен или не активен!", null)
                }
            }
        }
        layout.addView(btnOverlay)

        val btnLogs = Button(this).apply {
            text = "Просмотр Диагностических Логов"
            setOnClickListener {
                try {
                    startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
                } catch (e: Exception) {
                    logError("UI", "Ошибка открытия LogViewerActivity", e)
                }
            }
        }
        layout.addView(btnLogs)

        val btnHelp = Button(this).apply {
            text = "Справка по приложению"
            setOnClickListener {
                val service = MyAutoClickService.instance
                if (service != null) {
                    service.overlayManager.infoHelpDialog.show()
                } else {
                    logError("UI", "Служба не заложена, откройте оверлей после запуска службы", null)
                }
            }
        }
        layout.addView(btnHelp)

        setContentView(layout)
        logDiagnostic("UI", "MainActivity успешно инициализирована.")
    }
}
"""

print("=== ОБНОВЛЕНИЕ СПРАВКИ И РУКОВОДСТВА ПОЛЬЗОВАТЕЛЯ ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== СПРАВКА УСПЕШНО ОБНОВЛЕНА ===")