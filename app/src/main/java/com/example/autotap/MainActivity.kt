package com.example.autotap

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
