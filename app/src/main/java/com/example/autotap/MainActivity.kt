package com.example.autotap

import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
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

        try {
            setContentView(R.layout.activity_main)
            logDiagnostic("UI", "Главное меню успешно надуло activity_main.xml")
        } catch (e: Exception) {
            logError("UI", "Ошибка установки setContentView(R.layout.activity_main)", e)
        }

        val root = window.decorView.findViewById<View>(android.R.id.content)

        (root.findViewByNames("tvVersion") as? TextView)?.text = "v37 Precision Architecture"
        (root.findViewByNames("tvSubTitle") as? TextView)?.text = "Комплекс Автоматизации и ИИ Поиска"

        root.bindClickByNames("btnStartPanel") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.showControlPanel()
                logDiagnostic("UI", "Запуск панели оверлеев.")
            } else {
                Toast.makeText(this, "Сначала включите Accessibility Service!", Toast.LENGTH_LONG).show()
                logError("UI", "MyAutoClickService не запущен!", null)
            }
        }

        root.bindClickByNames("btnAccessibility") {
            try {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                logDiagnostic("UI", "Переход в настройки Accessibility.")
            } catch (e: Exception) {
                logError("UI", "Ошибка перехода в настройки Accessibility", e)
            }
        }

        root.bindClickByNames("btnOverlay") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this@MainActivity)) {
                try {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivity(intent)
                    logDiagnostic("UI", "Запрос разрешения оверлея.")
                } catch (e: Exception) {
                    logError("UI", "Ошибка запроса разрешения оверлея", e)
                }
            } else {
                Toast.makeText(this, "Разрешение оверлея уже предоставлено!", Toast.LENGTH_SHORT).show()
            }
        }

        root.bindClickByNames("btnAppDetails", "btnPermissionsHelp") {
            openRestrictedSettingsMenu()
        }

        root.bindClickByNames("btnShowLogs") {
            try {
                startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
            } catch (e: Exception) {
                logError("UI", "Ошибка открытия LogViewerActivity", e)
            }
        }

        root.bindClickByNames("btnInfoHelp") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.infoHelpDialog.show()
            }
        }

        root.bindClickByNames("btnManageTemplates") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.templatesManagerDialog.show()
            }
        }

        root.bindClickByNames("btnExport", "btnImport") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.exportImportDialog.show()
            }
        }

        updateUIStatusIndicators()
    }

    override fun onResume() {
        super.onResume()
        updateUIStatusIndicators()
    }

    private fun openRestrictedSettingsMenu() {
        try {
            val intent = Intent(
                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:$packageName")
            )
            startActivity(intent)
            Toast.makeText(
                this,
                "Нажмите 3 точки в правом верхнем углу и выберите 'Разрешить ограниченные настройки'",
                Toast.LENGTH_LONG
            ).show()
            logDiagnostic("UI", "Открыто меню снятия ограничений Restricted Settings.")
        } catch (e: Exception) {
            logError("UI", "Ошибка открытия настроек приложения", e)
        }
    }

    private fun updateUIStatusIndicators() {
        val root = window.decorView.findViewById<View>(android.R.id.content)
        val isServiceActive = MyAutoClickService.instance != null
        val hasOverlay = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) Settings.canDrawOverlays(this) else true

        (root.findViewByNames("btnAccessibility") as? Button)?.apply {
            text = if (isServiceActive) "1. Accessibility: [ ВКЛ ]" else "1. Accessibility: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (isServiceActive) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnOverlay") as? Button)?.apply {
            text = if (hasOverlay) "2. Оверлеи: [ ВКЛ ]" else "2. Оверлеи: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (hasOverlay) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnPermissionsHelp", "btnAppDetails") as? Button)?.apply {
            text = "3. Снятие ограничений"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
        }
    }

    private fun initRepositories() {
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)
    }

    private fun initEngines() {
        actionEditorEngine = ActionEditorEngine()
    }
}
