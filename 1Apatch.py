import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Обновлен ресурс/код: {rel_path}")

def fix_hints_and_descriptions():
    print("🚀 Восстановление подсказок и обновление текстов описания v35.0.0 Enterprise...")

    # 1. app/build.gradle.kts
    gradle_code = r"""plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.autotap"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.autotap"
        minSdk = 24
        targetSdk = 35
        versionCode = 2500
        versionName = "35.0.0-PRO"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("com.google.android.material:material:1.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
"""
    write_file("app/build.gradle.kts", gradle_code)

    # 2. strings.xml (Описание службы доступности)
    strings_code = r"""<resources>
    <string name="app_name">AutoTap</string>
    <string name="accessibility_description">Служба автоматизации AutoTap v35 Enterprise: нативные тапы, траектории жестов, ИИ-сканер с калибровкой и авто-обучением масок.</string>
</resources>
"""
    write_file("app/src/main/res/values/strings.xml", strings_code)

    # 3. MyAutoClickService.kt (100% интерактивные подсказки showTutorialCard)
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.PointF
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Typeface
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.FileProvider
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScenarioRunner
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ClickVisualizerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.ScriptsDialog
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.math.abs

class MyAutoClickService : AccessibilityService() {

    companion object {
        var instance: MyAutoClickService? = null

        fun logError(ctx: Context, e: Throwable) {
            try {
                val file = File(ctx.filesDir, "error_log.txt")
                file.appendText("\n\n${System.currentTimeMillis()}:\n${e.stackTraceToString()}")
            } catch (_: Exception) {}
        }

        fun logAppEvent(ctx: Context, tag: String, msg: String) {
            try {
                val file = File(ctx.filesDir, "app_events.txt")
                file.appendText("\n[$tag] $msg")
            } catch (_: Exception) {}
        }
    }

    // --- CORE SUBSYSTEMS ---
    lateinit var overlayManager: OverlayManager
    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var scenarioRunner: ScenarioRunner
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // --- UI OVERLAYS ---
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay
    lateinit var clickVisualizerOverlay: ClickVisualizerOverlay

    // --- STATE ---
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplates: ArrayList<Bitmap>
        get() = templateRepository.globalTemplates

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        templateRepository = TemplateRepository.init(this)
        scriptRepository = ScriptRepository.init(this)

        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        scenarioRunner = ScenarioRunner(this)
        aiScannerEngine = AiScannerEngine(this)

        controlPanelOverlay = ControlPanelOverlay(this)
        joystickOverlay = JoystickOverlay(this)
        captureFrameOverlay = CaptureFrameOverlay(this)
        debuggerOverlay = ScenarioDebuggerOverlay(this)
        clickVisualizerOverlay = ClickVisualizerOverlay(this)

        templateRepository.loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v35.0.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    fun vibrateFeedback(ms: Long = 25L) = gestureExecutor.vibrateFeedback(ms)

    fun getRealScreenSize(): Pair<Int, Int> = overlayManager.getRealScreenSize()
    fun dpToPx(dp: Int): Int = overlayManager.dpToPx(dp)
    fun dpToPx(dp: Float): Int = overlayManager.dpToPx(dp)

    fun showControlPanel() = controlPanelOverlay.show()

    fun hideControlPanel(openMainApp: Boolean = false) {
        controlPanelOverlay.hide()
        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) { logError(this, e) }
        }
    }

    fun showFloatingStopButton() = controlPanelOverlay.showFloatingStopButton()
    fun hideFloatingStopButton() = controlPanelOverlay.hideFloatingStopButton()

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))
        if (actionsList.isEmpty()) {
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        scenarioRunner.start()
    }

    fun stopExecutionLoop() {
        scenarioRunner.stop()
    }

    fun startOverlayRecording() {
        isRecording = true
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        controlPanelOverlay.hide()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        controlPanelOverlay.show()
        hideFloatingStopButton()
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    fun toggleNumbersVisibility() {
        isNumbersHidden = !isNumbersHidden
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
        Toast.makeText(this, if (isNumbersHidden) "👁 Номера скрыты" else "👁 Номера показаны", Toast.LENGTH_SHORT).show()
    }

    fun clearAllActions() {
        actionsList.forEach { act ->
            act.startView?.let { overlayManager.safeRemoveView(it) }
            act.endView?.let { overlayManager.safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(x: Float, y: Float, delay: Long, type: ActionType, id: Int) {
        val cfg = ActionConfig(
            id = if (id == -1) (actionsList.size + 1) else id,
            type = type,
            xNorm = normalizeX(x),
            yNorm = normalizeY(y),
            delay = delay
        )
        actionsList.add(cfg)
    }

    fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = overlayManager.dpToPx(36)
        val params = overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        config.endView = endView
        overlayManager.safeAddView(endView, params)
    }

    fun normalizeX(px: Float): Float {
        val (w, _) = overlayManager.getRealScreenSize()
        return (px / w.toFloat()).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val (_, h) = overlayManager.getRealScreenSize()
        return (px / h.toFloat()).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val (w, h) = overlayManager.getRealScreenSize()
        return Pair((nx * w).coerceIn(0f, w.toFloat()), (ny * h).coerceIn(0f, h.toFloat()))
    }

    fun randomOffset(radius: Int): PointF = gestureExecutor.randomOffset(radius)

    fun performClickWithCallback(x: Float, y: Float, duration: Long = globalClickDurationMs, onComplete: ((Boolean) -> Unit)? = null) {
        gestureExecutor.performClickWithCallback(x, y, duration, onComplete)
    }

    fun showClickVisualizer(x: Float, y: Float) = clickVisualizerOverlay.showClickAt(x, y)

    fun captureScreenBitmap(): Bitmap? = captureFrameOverlay.capture()

    fun showScriptsDialog() = ScriptsDialog(this).show()
    fun showEditDialog(config: ActionConfig) = EditActionDialog(this).show(config)

    fun showScriptPickerDialog(title: String, onSelected: (String) -> Unit) {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_select_script_for_export, null)
        val tvTitle = dialogView.findViewById<TextView>(R.id.tvPickerTitle)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutPickerList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnClosePicker)

        tvTitle?.text = title
        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val dir = File(filesDir, "scripts")
        if (dir.exists()) {
            dir.listFiles()?.forEach { file ->
                if (file.name.endsWith(".json")) {
                    val btn = Button(this).apply {
                        text = file.nameWithoutExtension
                        setTextColor(android.graphics.Color.WHITE)
                        setBackgroundColor(android.graphics.Color.parseColor("#1C2541"))
                        setOnClickListener {
                            onSelected(file.nameWithoutExtension)
                            overlayManager.safeRemoveView(dialogView)
                        }
                    }
                    layoutList?.addView(btn)
                }
            }
        }

        btnClose?.setOnClickListener { overlayManager.safeRemoveView(dialogView) }
        overlayManager.safeAddView(dialogView, params)
    }

    fun showAddActionMenu() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val btnClick = dialogView.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = dialogView.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = dialogView.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelAdd)

        val screenSize = overlayManager.getRealScreenSize()
        val spawnX = screenSize.first / 2f
        val spawnY = screenSize.second / 2f

        btnClick?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1); overlayManager.safeRemoveView(dialogView) }
        btnSwipe?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1); spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f); overlayManager.safeRemoveView(dialogView) }
        btnAi?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0); overlayManager.safeRemoveView(dialogView) }
        btnCancel?.setOnClickListener { vibrateFeedback(20L); overlayManager.safeRemoveView(dialogView) }

        overlayManager.safeAddView(dialogView, params)
    }

    fun showTutorialCard() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvTutTitle)
        val tvDesc = dialogView.findViewById<TextView>(R.id.tvTutDesc)
        val btnPrev = dialogView.findViewById<Button>(R.id.btnTutPrev)
        val btnNext = dialogView.findViewById<Button>(R.id.btnTutNext)
        val btnSkip = dialogView.findViewById<Button>(R.id.btnTutSkip)

        var step = 0
        val steps = listOf(
            Pair("1/5: Панель управления", "Кнопка ▶ запускает сценарий, + добавляет шаги, 📸 включает ИИ-прицел."),
            Pair("2/5: Настройка шагов", "Тапните по мишени на экране, чтобы изменить задержку, разброс или калибровку ИИ."),
            Pair("3/5: Живая запись", "Кнопка 🔴 в меню включает мгновенную запись ваших кликов и свайпов прямо по экрану."),
            Pair("4/5: ИИ-Сканер масок", "Кнопка 📸 вырезает любой элемент экрана. Кликер будет находить его автоматически!"),
            Pair("5/5: Менеджер сценариев", "Папка 📁 сохраняет наборы шагов в файлы, делает авто-бэкапы и экспортирует в ZIP.")
        )

        fun updateContent() {
            tvTitle?.text = steps[step].first
            tvDesc?.text = steps[step].second
            btnPrev?.visibility = if (step > 0) View.VISIBLE else View.INVISIBLE
            btnNext?.text = if (step < steps.size - 1) "Далее ►" else "Готово ✔"
        }

        updateContent()

        btnPrev?.setOnClickListener {
            vibrateFeedback(20L)
            if (step > 0) {
                step--
                updateContent()
            }
        }

        btnNext?.setOnClickListener {
            vibrateFeedback(20L)
            if (step < steps.size - 1) {
                step++
                updateContent()
            } else {
                overlayManager.safeRemoveView(dialogView)
            }
        }

        btnSkip?.setOnClickListener {
            vibrateFeedback(20L)
            overlayManager.safeRemoveView(dialogView)
        }

        overlayManager.safeAddView(dialogView, params)
    }

    fun loadScriptByName(name: String): List<ActionConfig> = scriptRepository.loadScriptByName(name)
    fun saveScriptByName(name: String, actions: List<ActionConfig>) = scriptRepository.saveScriptByName(name, actions)

    fun loadAllTemplatesFromDisk() = templateRepository.loadAllTemplatesFromDisk()
    fun moveTemplateToTrash(index: Int) = templateRepository.moveTemplateToTrash(index)
    fun exportScriptWithTemplates(context: Context, scriptName: String) = scriptRepository.exportScriptWithTemplates(scriptName)

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        super.onDestroy()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    # 4. MainActivity.kt (Инфо-диалоги и тексты)
    main_activity_code = r"""package com.example.autotap

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.StrictMode
import android.provider.Settings
import android.view.LayoutInflater
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import java.io.*
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

@Suppress("SpellCheckingInspection", "DEPRECATION")
class MainActivity : AppCompatActivity() {

    private var hasAutoShownPermissions = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        StrictMode.setVmPolicy(StrictMode.VmPolicy.Builder().build())

        val tvVersion = findViewById<TextView>(R.id.tvVersion)
        tvVersion?.text = "AutoTap v35.0.0-PRO"

        val btnAppDetails = findViewById<Button>(R.id.btnAppDetails)
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)
        val btnExport = findViewById<Button>(R.id.btnExport)
        val btnImport = findViewById<Button>(R.id.btnImport)
        val btnStartPanel = findViewById<Button>(R.id.btnStartPanel)
        val btnShowLogs = findViewById<Button>(R.id.btnShowLogs)
        val btnManageTemplates = findViewById<Button>(R.id.btnManageTemplates)
        val btnPermissionsHelp = findViewById<Button>(R.id.btnPermissionsHelp)
        val btnInfoHelp = findViewById<Button>(R.id.btnInfoHelp)

        btnAppDetails?.setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            })
        }

        btnAccessibility?.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        btnOverlay?.setOnClickListener {
            try {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            } catch (_: Exception) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION))
            }
        }

        btnExport?.setOnClickListener { showExportDialog() }
        btnImport?.setOnClickListener { startImportFlow() }
        btnShowLogs?.setOnClickListener { showLogsDialog() }
        btnManageTemplates?.setOnClickListener { showTemplatesManagerDialog() }
        btnPermissionsHelp?.setOnClickListener { showPermissionsHelpDialog() }
        btnInfoHelp?.setOnClickListener { showInfoHelpDialog() }

        btnStartPanel?.setOnClickListener {
            val service = MyAutoClickService.instance
            if (service == null) {
                Toast.makeText(this, "Служба не активна!", Toast.LENGTH_SHORT).show()
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                return@setOnClickListener
            }

            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Разрешите показ поверх окон!", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            service.showControlPanel()
            moveTaskToBack(true)
        }
    }

    override fun onResume() {
        super.onResume()
        updatePermissionButtonStates()

        val isServiceRunning = MyAutoClickService.instance != null
        val isOverlayGranted = Settings.canDrawOverlays(this)

        if ((!isServiceRunning || !isOverlayGranted) && !hasAutoShownPermissions) {
            hasAutoShownPermissions = true
            showPermissionsHelpDialog()
        }
    }

    private fun updatePermissionButtonStates() {
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)

        val isServiceBound = MyAutoClickService.instance != null
        val isSystemEnabled = isAccessibilityServiceEnabled()
        val isOverlayGranted = Settings.canDrawOverlays(this)

        btnAccessibility?.text =
            if (isServiceBound) "Служба кликера: ВКЛЮЧЕНА"
            else if (isSystemEnabled) "Перезапустить службу"
            else "Разрешить работу кликера"

        btnAccessibility?.backgroundTintList =
            ColorStateList.valueOf(if (isServiceBound) Color.parseColor("#1E3A2B") else Color.parseColor("#8B0000"))

        btnOverlay?.text =
            if (isOverlayGranted) "Показ поверх окон: РАЗРЕШЕНО"
            else "Показ поверх окон: ОТКЛЮЧЕНО"

        btnOverlay?.backgroundTintList =
            ColorStateList.valueOf(if (isOverlayGranted) Color.parseColor("#1E3A2B") else Color.parseColor("#21262D"))
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val am = getSystemService(Context.ACCESSIBILITY_SERVICE) as? android.view.accessibility.AccessibilityManager
        val enabled = am?.getEnabledAccessibilityServiceList(
            android.accessibilityservice.AccessibilityServiceInfo.FEEDBACK_ALL_MASK
        ) ?: emptyList()

        if (enabled.any { it.resolveInfo.serviceInfo.packageName == packageName }) return true

        val raw = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: ""
        return raw.split(':').any { it.substringBefore('/').equals(packageName, true) }
    }

    private fun showExportDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_export_select, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        dialogView.findViewById<Button>(R.id.btnExpSingleScript)?.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        dialogView.findViewById<Button>(R.id.btnExpTemplatesOnly)?.setOnClickListener {
            ad.dismiss()
            exportTemplatesOnly()
        }

        dialogView.findViewById<Button>(R.id.btnExpFullBackup)?.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        dialogView.findViewById<Button>(R.id.btnCloseExpSelect)?.setOnClickListener {
            ad.dismiss()
        }

        ad.show()
    }

    private fun exportTemplatesOnly() {
        val baseDir = File(filesDir, "templates")
        if (!baseDir.exists() || baseDir.listFiles()?.isEmpty() == true) {
            Toast.makeText(this, "Пул шаблонов пуст!", Toast.LENGTH_SHORT).show()
            return
        }

        val zipFile = File(externalCacheDir ?: cacheDir, "autotap_templates.zip")
        zipFolder(baseDir, zipFile)
        shareZip(zipFile, "ИИ-шаблоны AutoTap")
    }

    private fun exportFullBackup() {
        try {
            val zipFile = File(externalCacheDir ?: cacheDir, "autotap_backup.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val scriptsDir = File(filesDir, "scripts")
            if (scriptsDir.exists()) zipDirToZip(filesDir, scriptsDir, zos)

            val templatesDir = File(filesDir, "templates")
            if (templatesDir.exists()) zipDirToZip(filesDir, templatesDir, zos)

            zos.close()
            shareZip(zipFile, "Полный бэкап AutoTap v35")
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка бэкапа!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun startImportFlow() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            type = "application/zip"
            addCategory(Intent.CATEGORY_OPENABLE)
        }
        startActivityForResult(intent, 1002)
    }

    override fun onActivityResult(req: Int, res: Int, data: Intent?) {
        super.onActivityResult(req, res, data)
        if (req == 1002 && res == RESULT_OK) {
            val uri = data?.data ?: return
            importZip(uri)
        }
    }

    private fun importZip(uri: Uri) {
        try {
            val input = contentResolver.openInputStream(uri) ?: return
            val zis = ZipInputStream(BufferedInputStream(input))

            var entry: ZipEntry?
            while (zis.nextEntry.also { entry = it } != null) {
                val name = entry!!.name
                val outFile = File(filesDir, name)

                outFile.parentFile?.mkdirs()
                BufferedOutputStream(FileOutputStream(outFile)).use { bos ->
                    zis.copyTo(bos)
                }
            }
            zis.close()

            MyAutoClickService.instance?.loadAllTemplatesFromDisk()
            Toast.makeText(this, "Импорт завершён!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка импорта!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun zipFolder(folder: File, zipFile: File) {
        val zos = ZipOutputStream(FileOutputStream(zipFile))
        folder.listFiles()?.forEach { file ->
            val entry = ZipEntry(file.name)
            zos.putNextEntry(entry)
            zos.write(file.readBytes())
            zos.closeEntry()
        }
        zos.close()
    }

    private fun zipDirToZip(root: File, src: File, zos: ZipOutputStream) {
        src.listFiles()?.forEach { file ->
            if (file.isDirectory) {
                zipDirToZip(root, file, zos)
            } else {
                val entryName = file.absolutePath.substring(root.absolutePath.length + 1)
                zos.putNextEntry(ZipEntry(entryName))
                zos.write(file.readBytes())
                zos.closeEntry()
            }
        }
    }

    private fun shareZip(zipFile: File, title: String) {
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", zipFile)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, title))
    }

    private fun showLogsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_logs, null)
        val tvLogs = dialogView.findViewById<TextView>(R.id.tvLogsContent)
        val btnShare = dialogView.findViewById<Button>(R.id.btnShareLogs)
        val btnClear = dialogView.findViewById<Button>(R.id.btnClearLogs)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseLogs)

        val logFile = File(filesDir, "error_log.txt")
        tvLogs?.text = if (logFile.exists() && logFile.length() > 0) logFile.readText() else "Логи отсутствуют."

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        btnShare?.setOnClickListener {
            if (logFile.exists() && logFile.length() > 0) {
                val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", logFile)
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                startActivity(Intent.createChooser(intent, "Поделиться логами"))
            } else {
                Toast.makeText(this, "Логи пусты", Toast.LENGTH_SHORT).show()
            }
        }

        btnClear?.setOnClickListener {
            if (logFile.exists()) logFile.delete()
            tvLogs?.text = "Логи очищены."
            Toast.makeText(this, "Логи очищены", Toast.LENGTH_SHORT).show()
        }

        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showTemplatesManagerDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_templates_manager, null)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutTemplatesList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseTemplatesManager)

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        fun refresh() {
            layoutList?.removeAllViews()
            val baseDir = File(filesDir, "templates")

            baseDir.listFiles()?.forEach { folder ->
                if (folder.isDirectory) {
                    folder.listFiles()?.forEach { file ->
                        if (file.name.startsWith("mask_") && file.name.endsWith(".png")) {
                            val item = LayoutInflater.from(this).inflate(R.layout.item_template, null)

                            val iv = item.findViewById<ImageView>(R.id.ivTemplatePreview)
                            val tv = item.findViewById<TextView>(R.id.tvTemplateName)
                            val btnDelete = item.findViewById<Button>(R.id.btnDeleteTemplateFile)

                            iv?.setImageBitmap(BitmapFactory.decodeFile(file.absolutePath))
                            tv?.text = "${folder.name}\n${file.nameWithoutExtension}"

                            btnDelete?.setOnClickListener {
                                MyAutoClickService.instance?.moveTemplateToTrash(
                                    MyAutoClickService.instance?.globalTemplatesNames?.indexOf(file.absolutePath) ?: -1
                                )
                                MyAutoClickService.instance?.loadAllTemplatesFromDisk()
                                refresh()
                            }

                            layoutList?.addView(item)
                        }
                    }
                }
            }
        }

        refresh()
        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showPermissionsHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_permissions, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()
        dialogView.findViewById<Button>(R.id.btnClosePermissionsDialog)?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showInfoHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_info, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        val tvContent = dialogView.findViewById<TextView>(R.id.tvTabContent)
        val tabClick = dialogView.findViewById<Button>(R.id.tabClick)
        val tabSwipe = dialogView.findViewById<Button>(R.id.tabSwipe)
        val tabAi = dialogView.findViewById<Button>(R.id.tabAi)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseInfoDialog)

        val clickInfo = "• Клики (Click):\nТочечное нажатие по координатам с регулируемой задержкой, повторами и случайным разбросом.\n\n• Зажатие (Hold):\nУдержание точки на заданное время (в мс)."
        val swipeInfo = "• Свайпы (Swipe):\nПлавное перемещение от точки (S) к (E).\n\n• Траектория Джойстика:\nЗапись сложных свайпов через плавающий джойстик."
        val aiInfo = "• ИИ-Сканер (AI Trigger v35):\nПоиск заданного изображения на экране с калибровкой, выбором порога (%) и эстафетой сценариев."

        tvContent?.text = clickInfo

        tabClick?.setOnClickListener {
            tvContent?.text = clickInfo
            tabClick.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
        }

        tabSwipe?.setOnClickListener {
            tvContent?.text = swipeInfo
            tabClick?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
        }

        tabAi?.setOnClickListener {
            tvContent?.text = aiInfo
            tabClick?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
        }

        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MainActivity.kt", main_activity_code)

    print("✨ Подсказки, справочные экраны и описания v35 успешно обновлены!")

if __name__ == "__main__":
    fix_hints_and_descriptions()