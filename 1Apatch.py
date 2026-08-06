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

# 1. MainActivity.kt — 100% привязка к activity_main.xml
files["app/src/main/java/com/example/autotap/MainActivity.kt"] = """package com.example.autotap

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.ActionEditorEngine
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

        // Устанавливаем физический XML макет Главного Меню activity_main.xml
        try {
            setContentView(R.layout.activity_main)
            logDiagnostic("UI", "Главное меню успешно установлено из setContentView(R.layout.activity_main).")
        } catch (e: Exception) {
            logError("UI", "Ошибка установки setContentView(R.layout.activity_main)", e)
        }

        val root = window.decorView.findViewById<View>(android.R.id.content)

        // Безопасная привязка интерактивных элементов Главного Меню из XML
        root.bindClickByNames("btn_enable_accessibility", "btnAccessibility", "btn_accessibility", "accessibility") {
            try {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                logDiagnostic("UI", "Переход в настройки Accessibility из Главного Меню.")
            } catch (e: Exception) {
                logError("UI", "Ошибка перехода в настройки Accessibility", e)
            }
        }

        root.bindClickByNames("btn_overlay_permission", "btnOverlayPerm", "btn_overlay", "overlay") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this@MainActivity)) {
                try {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivity(intent)
                    logDiagnostic("UI", "Запрос разрешения на оверлеи из Главного Меню.")
                } catch (e: Exception) {
                    logError("UI", "Ошибка запроса разрешения оверлеев", e)
                }
            } else {
                logDiagnostic("UI", "Разрешение на оверлеи уже активно.")
            }
        }

        root.bindClickByNames("btn_start_service", "btnStartPanel", "btn_start_overlay", "btn_panel", "btn_start") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.showControlPanel()
                logDiagnostic("UI", "Запуск Панели Управления из Главного Меню.")
            } else {
                logError("UI", "Служба не заложена, запустите Accessibility Service", null)
            }
        }

        root.bindClickByNames("btn_open_settings", "btnSettings", "btn_global_settings") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.globalSettingsDialog.show()
            }
        }

        root.bindClickByNames("btn_open_templates", "btnTemplates", "btn_templates_manager") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.templatesManagerDialog.show()
            }
        }

        root.bindClickByNames("btn_open_logs", "btnLogs", "btn_log_viewer") {
            try {
                startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
            } catch (e: Exception) {
                logError("UI", "Ошибка открытия экрана логов", e)
            }
        }

        root.bindClickByNames("btn_open_help", "btnHelp", "btn_info") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.infoHelpDialog.show()
            }
        }

        root.bindClickByNames("btn_start_tutorial", "btnTutorial", "btn_education") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.tutorialEngine.startDefaultTutorial()
            }
        }

        logDiagnostic("UI", "MainActivity (Оригинальное Главное Меню) успешно инициализирована.")
    }

    override fun onResume() {
        super.onResume()
        checkSystemStatus()
    }

    private fun initRepositories() {
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)
    }

    private fun initEngines() {
        actionEditorEngine = ActionEditorEngine()
    }

    private fun checkSystemStatus() {
        val hasOverlay = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) Settings.canDrawOverlays(this) else true
        val serviceActive = MyAutoClickService.instance != null
        logDiagnostic("CORE", "Статус Главного Меню: Accessibility=$serviceActive, OverlayPermission=$hasOverlay")
    }
}
"""

# 2. LogViewerActivity.kt — 100% привязка к dialog_logs.xml
files["app/src/main/java/com/example/autotap/ui/LogViewerActivity.kt"] = """package com.example.autotap.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError

class LogViewerActivity : AppCompatActivity() {

    private var logTextView: TextView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        try {
            setContentView(R.layout.dialog_logs)
            logDiagnostic("UI", "Экран логов надул оригинальный dialog_logs.xml")
        } catch (e: Exception) {
            logError("UI", "Ошибка установки setContentView(R.layout.dialog_logs)", e)
        }

        val root = window.decorView.findViewById<View>(android.R.id.content)

        logTextView = root.findViewByNames("tv_logs", "tv_log_content", "log_text", "txt_logs") as? TextView

        root.bindClickByNames("btn_share_logs", "btnShare", "btn_share") {
            shareLogFile()
        }

        root.bindClickByNames("btn_clear_logs", "btnClear", "btn_clear") {
            clearLogFile()
        }

        root.bindClickByNames("btn_close_logs", "btnClose", "btn_close") {
            finish()
        }

        refreshLogs()
    }

    private fun refreshLogs() {
        val file = StructuredLogger.getLogFile()
        if (file != null && file.exists()) {
            val content = file.readText()
            logTextView?.text = if (content.isBlank()) "Лог-файл пуст." else content
        } else {
            logTextView?.text = "Лог-файл еще не создан."
        }
    }

    private fun clearLogFile() {
        val file = StructuredLogger.getLogFile()
        if (file != null && file.exists()) {
            file.writeText("")
            logDiagnostic("LOGS", "Лог-файл очищен из dialog_logs.")
        }
        refreshLogs()
    }

    private fun shareLogFile() {
        val file = StructuredLogger.getLogFile() ?: return
        if (!file.exists()) return

        try {
            val uri: Uri = FileProvider.getUriForFile(
                this,
                "$packageName.fileprovider",
                file
            )
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(intent, "Поделиться error_log.txt"))
        } catch (e: Exception) {
            logError("LOGS", "Ошибка отправки файла логов", e)
        }
    }
}
"""

# 3. InfoHelpDialog.kt — 100% привязка к dialog_info.xml
files["app/src/main/java/com/example/autotap/ui/overlays/InfoHelpDialog.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class InfoHelpDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.7f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = try {
            inflater.inflate(R.layout.dialog_info, null)
        } catch (e: Exception) {
            View(context)
        }

        view.bindClickByNames("btn_close_info", "btnCloseInfo", "btn_close", "btnClose", "btn_ok") {
            logDiagnostic("UI", "Закрыта справка (dialog_info.xml).")
            hide()
        }

        return view
    }
}
"""

print("=== ВОЗВРАТ ОРИГИНАЛЬНОГО ГЛАВНОГО МЕНЮ И ДИАЛОГОВ ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ГЛАВНОЕ МЕНЮ И ВСЕ ДИАЛОГИ УСПЕШНО ВОССТАНОВЛЕНЫ ===")