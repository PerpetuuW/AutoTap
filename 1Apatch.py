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

# 1. OverlayBase.kt — Добавление поддержки выреза чёлки LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
files["app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt"] = """package com.example.autotap.ui.base

import android.content.Context
import android.graphics.Rect
import android.os.Build
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.createOverlayParams
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.safeAddView
import com.example.autotap.safeRemoveView

abstract class OverlayBase(
    protected val context: Context,
    val overlayManager: OverlayManager
) {
    protected val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    var width: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var height: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var gravity: Int = Gravity.TOP or Gravity.START
    var flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
    var dimAmount: Float = 0.5f

    var initialX: Int = 100
    var initialY: Int = 200

    var layer: OverlayLayer = OverlayLayer.PANEL_LAYER
    var priority: OverlayPriority = OverlayPriority.MEDIUM

    protected var overlayView: View? = null
    protected var layoutParams: WindowManager.LayoutParams? = null
    var isShowing: Boolean = false
        protected set

    abstract fun createView(): View

    open fun show() {
        if (isShowing) return
        try {
            val view = createView()
            view.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            overlayView = view
            val params = createOverlayParams(
                width = width,
                height = height,
                gravity = gravity,
                flags = flags,
                x = initialX,
                y = initialY
            ).apply {
                if (this@OverlayBase.dimAmount > 0f && (flags and WindowManager.LayoutParams.FLAG_DIM_BEHIND) != 0) {
                    this.dimAmount = this@OverlayBase.dimAmount
                }
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    this.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
                }
            }
            this.layoutParams = params
            val added = windowManager.safeAddView(view, params)
            if (added) {
                isShowing = true
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) отображен с поддержкой Cutout.")
            }
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка при отображении ${javaClass.simpleName}", e)
        }
    }

    open fun hide() {
        val view = overlayView ?: return
        if (isShowing) {
            try {
                windowManager.safeRemoveView(view)
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} скрыт.")
            } catch (e: Exception) {
                logError("OVERLAY", "Ошибка при скрытии ${javaClass.simpleName}", e)
            }
            overlayView = null
            isShowing = false
        }
    }

    fun setTouchable(touchable: Boolean) {
        val lp = layoutParams ?: return
        val view = overlayView ?: return
        if (touchable) {
            lp.flags = lp.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
        } else {
            lp.flags = lp.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
        }
        try {
            windowManager.updateViewLayout(view, lp)
            logDiagnostic("OVERLAY", "Флаг touchable для ${javaClass.simpleName} установлен в $touchable")
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления флага touchable", e)
        }
    }

    fun getBounds(): Rect {
        val lp = layoutParams ?: return Rect(0, 0, 0, 0)
        val w = if (width > 0) width else 200
        val h = if (height > 0) height else 200
        return Rect(lp.x, lp.y, lp.x + w, lp.y + h)
    }

    protected fun setupDragAndDrop(view: View) {
        var startX = 0
        var startY = 0
        var touchX = 0f
        var touchY = 0f

        view.setOnTouchListener { _, event ->
            val lp = layoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = lp.x
                    startY = lp.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    lp.x = startX + (event.rawX - touchX).toInt()
                    lp.y = startY + (event.rawY - touchY).toInt()
                    try {
                        windowManager.updateViewLayout(view, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка перемещения оверлея", e)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
"""

# 2. MainActivity.kt — Оркестратор системы AutoTap v35/v37
files["app/src/main/java/com/example/autotap/MainActivity.kt"] = """package com.example.autotap

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.engine.ScenarioRunner
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.LogViewerActivity

class MainActivity : AppCompatActivity() {

    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository
    lateinit var actionEditorEngine: ActionEditorEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        StructuredLogger.init(this)

        initRepositories()
        initEngines()

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        val titleText = TextView(this).apply {
            text = "AutoTap v35/v37 Systems Orchestrator"
            textSize = 18f
            setPadding(0, 0, 0, 16)
        }
        layout.addView(titleText)

        val btnAccessibility = Button(this).apply {
            text = "1. Включить Accessibility Service"
            setOnClickListener {
                try {
                    startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                    logDiagnostic("UI", "Переход в настройки Accessibility.")
                } catch (e: Exception) {
                    logError("UI", "Ошибка перехода в настройки Accessibility", e)
                }
            }
        }
        layout.addView(btnAccessibility)

        val btnOverlayPerm = Button(this).apply {
            text = "2. Разрешение на Overlay (Оверлеи)"
            setOnClickListener {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this@MainActivity)) {
                    try {
                        val intent = Intent(
                            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:$packageName")
                        )
                        startActivity(intent)
                        logDiagnostic("UI", "Запрос разрешения на оверлеи.")
                    } catch (e: Exception) {
                        logError("UI", "Ошибка запроса разрешения оверлея", e)
                    }
                } else {
                    logDiagnostic("UI", "Разрешение на оверлеи уже предоставлено.")
                }
            }
        }
        layout.addView(btnOverlayPerm)

        val btnStartOverlay = Button(this).apply {
            text = "3. Запустить Панель Оверлеев"
            setOnClickListener {
                val service = MyAutoClickService.instance
                if (service != null) {
                    service.showControlPanel()
                    logDiagnostic("UI", "Панель управления успешно запущена из MainActivity.")
                } else {
                    logError("UI", "MyAutoClickService не запущен! Сначала включите Accessibility Service.", null)
                }
            }
        }
        layout.addView(btnStartOverlay)

        val btnTutorial = Button(this).apply {
            text = "4. Запустить Обучение (Tutorial)"
            setOnClickListener {
                val service = MyAutoClickService.instance
                if (service != null) {
                    service.tutorialEngine.startDefaultTutorial()
                    logDiagnostic("UI", "Запущен интерактивный туториал из MainActivity.")
                } else {
                    logError("UI", "Служба Accessibility не активна для запуска туториала.", null)
                }
            }
        }
        layout.addView(btnTutorial)

        val btnLogs = Button(this).apply {
            text = "5. Диагностические Логи"
            setOnClickListener {
                try {
                    startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
                } catch (e: Exception) {
                    logError("UI", "Ошибка открытия экрана логов LogViewerActivity", e)
                }
            }
        }
        layout.addView(btnLogs)

        val btnHelp = Button(this).apply {
            text = "6. Справка по приложению"
            setOnClickListener {
                val service = MyAutoClickService.instance
                if (service != null) {
                    service.overlayManager.infoHelpDialog.show()
                } else {
                    logError("UI", "Запустите службу для показа оверлея справки.", null)
                }
            }
        }
        layout.addView(btnHelp)

        setContentView(layout)
        logDiagnostic("UI", "MainActivity (Оркестратор системы) успешно инициализирована.")
    }

    override fun onResume() {
        super.onResume()
        checkSystemStatus()
    }

    private fun initRepositories() {
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)
        logDiagnostic("CORE", "Репозитории инициализированы в MainActivity.")
    }

    private fun initEngines() {
        actionEditorEngine = ActionEditorEngine()
        logDiagnostic("CORE", "Движки приложения инициализированы в MainActivity.")
    }

    private fun checkSystemStatus() {
        val hasOverlay = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) Settings.canDrawOverlays(this) else true
        val serviceActive = MyAutoClickService.instance != null
        logDiagnostic("CORE", "Статус системы: Accessibility=$serviceActive, OverlayPermission=$hasOverlay")
    }
}
"""

print("=== ВНЕДРЕНИЕ ОРКЕСТРАТОРА MainActivity И CUTOUT ПОДДЕРЖКИ ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ОРКЕСТРАТОР УСПЕШНО ОБНОВЛЕН ===")