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

        val versionName = try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: getString(R.string.app_version)
        } catch (_: Exception) {
            getString(R.string.app_version)
        }

        (root.findViewByNames("tvVersion") as? TextView)?.text = versionName
        (root.findViewByNames("tvSubTitle") as? TextView)?.text = "Комплекс Автоматизации и ИИ Поиска"

        root.bindClickByNames("btnStartPanel") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.showControlPanel()
                logDiagnostic("UI", "Запуск панели оверлеев.")
            } else {
                Toast.makeText(this, "Сначала включите Раздел 'Спец. возможности'!", Toast.LENGTH_LONG).show()
                logError("UI", "MyAutoClickService не запущен!", null)
            }
        }

        root.bindClickByNames("btnAccessibility") {
            try {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                logDiagnostic("UI", "Переход в системное меню Спец. возможности.")
            } catch (e: Exception) {
                logError("UI", "Ошибка перехода в Спец. возможности", e)
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
                    logDiagnostic("UI", "Запрос разрешения Поверх других приложений.")
                } catch (e: Exception) {
                    logError("UI", "Ошибка запроса разрешения Поверх других приложений", e)
                }
            } else {
                Toast.makeText(this, "Разрешение 'Поверх других приложений' уже предоставлено!", Toast.LENGTH_SHORT).show()
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
                "Найдите в самом низу экрана (или в меню 3 точек вверху) пункт 'Разрешить ограниченные настройки' и включите его",
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
            text = if (isServiceActive) "1. Спец. возможности: [ ВКЛ ]" else "1. Спец. возможности: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (isServiceActive) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnOverlay") as? Button)?.apply {
            text = if (hasOverlay) "2. Поверх других приложений: [ ВКЛ ]" else "2. Поверх других приложений: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (hasOverlay) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnPermissionsHelp", "btnAppDetails") as? Button)?.apply {
            text = "3. Ограниченные настройки (в самом низу)"
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
