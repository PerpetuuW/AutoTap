package com.example.autotap

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
