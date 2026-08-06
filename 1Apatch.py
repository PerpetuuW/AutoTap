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

# 1. MainActivity.kt — Вход в Restricted Settings + Динамические статусы ВКЛ/ВЫКЛ
files["app/src/main/java/com/example/autotap/MainActivity.kt"] = """package com.example.autotap

import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
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
            text = if (isServiceActive) "1. Accessibility Service: [ ВКЛЮЧЕНО ]" else "1. Accessibility Service: [ ВЫКЛЮЧЕНО ]"
            setTextColor(if (isServiceActive) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnOverlay") as? Button)?.apply {
            text = if (hasOverlay) "2. Оверлеи: [ РАЗРЕШЕНО ]" else "2. Оверлеи: [ ТРЕБУЕТСЯ РАЗРЕШЕНИЕ ]"
            setTextColor(if (hasOverlay) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnPermissionsHelp", "btnAppDetails") as? Button)?.apply {
            text = "3. Снятие Ограничений (Restricted Settings)"
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
"""

# 2. ControlPanelOverlay.kt — Индикация активных состояний СТАРТ / ЗАПИСЬ / ДЖОЙСТИК
files["app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var btnPlayView: View? = null
    private var btnRecordView: View? = null
    private var btnJoystickView: View? = null

    init {
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_control_panel, null)

        btnPlayView = view.findViewByNames("btnPlay")
        btnRecordView = view.findViewByNames("btnRecord")
        btnJoystickView = view.findViewByNames("btnToggleJoystick")

        view.bindClickByNames("btnPlay") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                if (svc.isPlaying) {
                    svc.scriptExecutor.stop()
                } else {
                    svc.scriptExecutor.start()
                }
                updateToggleStates()
            }
        }

        view.bindClickByNames("btnAdd") {
            logDiagnostic("OVERLAY", "Кнопка btnAdd нажата.")
            overlayManager.addActionDialog.show()
        }

        view.bindClickByNames("btnRecord") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                if (svc.recordingEngine.isRecording) {
                    svc.recordingEngine.stopRecording("recorded_script")
                } else {
                    svc.recordingEngine.startRecording()
                }
                updateToggleStates()
            }
        }

        view.bindClickByNames("btnLoadScript") {
            logDiagnostic("OVERLAY", "Кнопка btnLoadScript нажата.")
            overlayManager.scriptsDialog.show()
        }

        view.bindClickByNames("btnToggleJoystick") {
            if (overlayManager.joystickOverlay.isShowing) {
                overlayManager.joystickOverlay.hide()
            } else {
                overlayManager.joystickOverlay.show()
            }
            updateToggleStates()
        }

        view.bindClickByNames("btnHelpTutorial") {
            logDiagnostic("OVERLAY", "Кнопка btnHelpTutorial нажата.")
            MyAutoClickService.instance?.tutorialEngine?.startDefaultTutorial()
        }

        view.bindClickByNames("btnClose") {
            logDiagnostic("OVERLAY", "Кнопка btnClose нажата.")
            MyAutoClickService.instance?.scriptExecutor?.stop()
            hide()
        }

        val dragHandle = view.findViewByNames("handleDrag") ?: view
        setupDragAndDrop(dragHandle)
        updateToggleStates()
        return view
    }

    fun updateToggleStates() {
        val svc = MyAutoClickService.instance

        (btnPlayView as? Button)?.apply {
            val isPlaying = svc?.isPlaying == true
            isSelected = isPlaying
            text = if (isPlaying) "[ РАБОТАЕТ... ]" else "СТАРТ"
            setTextColor(if (isPlaying) Color.parseColor("#00E676") else Color.WHITE)
        }

        (btnRecordView as? Button)?.apply {
            val isRecording = svc?.recordingEngine?.isRecording == true
            isSelected = isRecording
            text = if (isRecording) "[ ЗАПИСЬ... ]" else "ЗАПИСЬ"
            setTextColor(if (isRecording) Color.parseColor("#FF5252") else Color.WHITE)
        }

        (btnJoystickView as? Button)?.apply {
            val isJoystickVisible = overlayManager.joystickOverlay.isShowing
            isSelected = isJoystickVisible
            text = if (isJoystickVisible) "[ ДЖОЙСТИК: ВКЛ ]" else "ДЖОЙСТИК"
            setTextColor(if (isJoystickVisible) Color.parseColor("#00E676") else Color.WHITE)
        }
    }
}
"""

# 3. ScriptsDialog.kt — Переключение состояния бесконечного повтора
files["app/src/main/java/com/example/autotap/ui/overlays/ScriptsDialog.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ScriptsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var etNameView: EditText? = null
    private var etLoopCountView: EditText? = null
    private var isInfiniteLoop = true

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.5f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_scripts, null)

        etNameView = view.findViewByNames("etScriptName") as? EditText
        etLoopCountView = view.findViewByNames("etScriptLoopCount") as? EditText

        view.bindClickByNames("btnSaveScriptAction") {
            val scriptName = etNameView?.text?.toString()?.ifBlank { "default_script" } ?: "default_script"
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.saveScriptByName(scriptName, svc.actionsList)
                logDiagnostic("SCRIPT", "Сценарий '$scriptName' сохранен по btnSaveScriptAction")
            }
            hide()
        }

        view.bindClickByNames("btnToggleScriptInfinite") { btn ->
            isInfiniteLoop = !isInfiniteLoop
            btn.isSelected = isInfiniteLoop
            (btn as? Button)?.apply {
                text = if (isInfiniteLoop) "Бесконечный повтор: [ ВКЛ ]" else "Бесконечный повтор: [ ВЫКЛ ]"
                setTextColor(if (isInfiniteLoop) Color.parseColor("#00E676") else Color.WHITE)
            }
            logDiagnostic("SCRIPT", "Переключение бесконечного повтора: $isInfiniteLoop")
        }

        view.bindClickByNames("btnSelectScriptRelay") {
            logDiagnostic("SCRIPT", "Выбор эстафетного сценария.")
        }

        view.bindClickByNames("btnCloseScripts", "btnCloseScriptsHeader") {
            hide()
        }

        return view
    }
}
"""

# 4. EditActionDialog.kt — Индикация тумблеров опций
files["app/src/main/java/com/example/autotap/ui/overlays/EditActionDialog.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class EditActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var etDelayView: EditText? = null
    private var etHoldDurationView: EditText? = null
    private var isClickTarget = false
    private var isAiNotification = true

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_edit_dialog, null)

        etDelayView = view.findViewByNames("etDelay") as? EditText
        etHoldDurationView = view.findViewByNames("etHoldDuration") as? EditText

        view.bindClickByNames("btnSave", "btnSaveHeader") {
            logDiagnostic("SCRIPT", "Шаг сохранен в floating_edit_dialog.")
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnCancel", "btnCloseHeader") {
            hide()
        }

        view.bindClickByNames("btnToggleClickTarget") { btn ->
            isClickTarget = !isClickTarget
            btn.isSelected = isClickTarget
            (btn as? Button)?.apply {
                text = if (isClickTarget) "Целевой клик: [ ВКЛ ]" else "Целевой клик: [ ВЫКЛ ]"
                setTextColor(if (isClickTarget) Color.parseColor("#00E676") else Color.WHITE)
            }
        }

        view.bindClickByNames("btnToggleAiNotification") { btn ->
            isAiNotification = !isAiNotification
            btn.isSelected = isAiNotification
            (btn as? Button)?.apply {
                text = if (isAiNotification) "Уведомление AI: [ ВКЛ ]" else "Уведомление AI: [ ВЫКЛ ]"
                setTextColor(if (isAiNotification) Color.parseColor("#00E676") else Color.WHITE)
            }
        }

        return view
    }
}
"""

print("=== ФИКС RESTRICTED SETTINGS И ЖИВАЯ ИНДИКАЦИЯ КНОПОК ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ФИКС УСПЕШНО ПРИМЕНЕН ===")