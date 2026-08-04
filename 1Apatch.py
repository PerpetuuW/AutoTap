import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан файл: {rel_path}")

def apply_control_panel_fix():
    print("🚀 Исправление ошибок ControlPanelOverlay и MyAutoClickService v28.19.0-PRO...")

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
        versionCode = 2342
        versionName = "28.19.0-PRO"

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

    # 2. MyAutoClickService.kt
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ScriptsDialog
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

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

    // CORE MODULES
    lateinit var overlayManager: OverlayManager
    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // UI OVERLAYS
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay

    // SCRIPT STATE
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    private val uiHandler = Handler(Looper.getMainLooper())

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        aiScannerEngine = AiScannerEngine(this)
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)

        controlPanelOverlay = ControlPanelOverlay(this)
        joystickOverlay = JoystickOverlay(this)
        captureFrameOverlay = CaptureFrameOverlay(this)
        debuggerOverlay = ScenarioDebuggerOverlay(this)

        templateRepository.loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v28.19.0 PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun vibrateFeedback(durationMs: Long = 25L) {
        gestureExecutor.vibrateFeedback(durationMs)
    }

    fun showControlPanel() {
        controlPanelOverlay.show()
    }

    fun hideControlPanel(openMainApp: Boolean = false) {
        controlPanelOverlay.hide()
        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) {
                logError(this, e)
            }
        }
    }

    fun showFloatingStopButton() {
        controlPanelOverlay.showFloatingStopButton()
    }

    fun hideFloatingStopButton() {
        controlPanelOverlay.hideFloatingStopButton()
    }

    fun showScriptsDialog() {
        ScriptsDialog(this).show()
    }

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))

        if (actionsList.isEmpty()) {
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }

        isPlaying = true
        scriptExecutor.startExecutionLoop()
    }

    fun stopExecutionLoop() {
        isPlaying = false
        scriptExecutor.stopExecutionLoop()
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

    fun captureScreenBitmap(): Bitmap? {
        return captureFrameOverlay.capture()
    }

    fun normalizeX(px: Float): Float {
        val dm = resources.displayMetrics
        return (px / dm.widthPixels).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val dm = resources.displayMetrics
        return (px / dm.heightPixels).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val dm = resources.displayMetrics
        return Pair(
            (nx * dm.widthPixels).coerceIn(0f, dm.widthPixels.toFloat()),
            (ny * dm.heightPixels).coerceIn(0f, dm.heightPixels.toFloat())
        )
    }

    fun randomOffset(radius: Int): PointF {
        if (radius <= 0) return PointF(0f, 0f)
        val dx = (-radius..radius).random().toFloat()
        val dy = (-radius..radius).random().toFloat()
        return PointF(dx, dy)
    }

    fun showClickVisualizer(x: Float, y: Float) {
        controlPanelOverlay.showClickVisualizer(x, y)
    }

    fun loadScriptByName(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))
    }

    fun moveTemplateToTrash(index: Int) {
        templateRepository.moveTemplateToTrash(index)
    }

    fun loadAllTemplatesFromDisk() {
        templateRepository.loadAllTemplatesFromDisk()
    }

    fun onCandidateSelected(point: PointF) {
        logAppEvent(this, "SELECTION", "Selected point: (${point.x}, ${point.y})")
    }

    fun exportScriptWithTemplates(context: Context, scriptName: String) {
        val scriptFile = File(File(filesDir, "scripts"), "$scriptName.json")
        if (!scriptFile.exists()) return
        val zipFile = File(externalCacheDir ?: cacheDir, "script_${scriptName}.zip")
        try {
            val zos = ZipOutputStream(FileOutputStream(zipFile))
            zos.putNextEntry(ZipEntry(scriptFile.name))
            zos.write(scriptFile.readBytes())
            zos.closeEntry()
            zos.close()
            shareZipFile(zipFile, "Сценарий $scriptName")
        } catch (e: Exception) {
            logError(this, e)
        }
    }

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

        val spawnOffset = (actionsList.size % 8) * overlayManager.dpToPx(24).toFloat()
        val spawnX = 350f + spawnOffset
        val spawnY = 350f + spawnOffset

        btnClick?.setOnClickListener {
            vibrateFeedback(20L)
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1)
            overlayManager.safeRemoveView(dialogView)
        }
        btnSwipe?.setOnClickListener {
            vibrateFeedback(20L)
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1)
            spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f)
            overlayManager.safeRemoveView(dialogView)
        }
        btnAi?.setOnClickListener {
            vibrateFeedback(20L)
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0)
            overlayManager.safeRemoveView(dialogView)
        }
        btnCancel?.setOnClickListener {
            vibrateFeedback(20L)
            overlayManager.safeRemoveView(dialogView)
        }

        overlayManager.safeAddView(dialogView, params)
    }

    fun showTutorialCard() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
        }

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvTutTitle)
        val tvDesc = dialogView.findViewById<TextView>(R.id.tvTutDesc)
        val btnPrev = dialogView.findViewById<Button>(R.id.btnTutPrev)
        val btnNext = dialogView.findViewById<Button>(R.id.btnTutNext)
        val btnSkip = dialogView.findViewById<Button>(R.id.btnTutSkip)

        var step = 0
        val steps = listOf(
            Pair("1/5: Главная панель", "Нажмите ▶ для запуска сценария, + для добавления клика, 📸 для ИИ-сканера."),
            Pair("2/5: Настройка шагов", "Тапните по круглой мишени на экране, чтобы изменить задержку, повторы или тип действия."),
            Pair("3/5: Запись жестов", "Нажмите 🔴 в меню, чтобы записывать ваши касания и свайпы прямо по экрану в реальном времени."),
            Pair("4/5: ИИ-Поиск", "Кнопка 📸 откроет прицел. Вырежьте любой элемент экрана, чтобы кликер находил его автоматически."),
            Pair("5/5: Скрипты", "Сохраняйте наборы шагов в файлы через папку 📁 и загружайте их в один клик.")
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

    private fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
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

    fun shareZipFile(zipFile: File, title: String) {
        try {
            val uri = androidx.core.content.FileProvider.getUriForFile(
                this,
                "$packageName.fileprovider",
                zipFile
            )

            val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(android.content.Intent.EXTRA_STREAM, uri)
                addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }

            startActivity(android.content.Intent.createChooser(intent, title))

        } catch (e: Exception) {
            logError(this, e)
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    # 3. ControlPanelOverlay.kt
    control_panel_code = r"""package com.example.autotap.ui.overlays

import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ControlPanelOverlay(private val service: MyAutoClickService) {

    private var panelView: View? = null
    private var stopButtonView: View? = null

    private var panelState = 0

    fun show() {
        if (panelView != null) {
            panelView?.visibility = View.VISIBLE
            return
        }

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_control_panel, null)
        panelView = view

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = service.overlayManager.dpToPx(20)
            y = service.overlayManager.dpToPx(120)
        }

        bindUi(view)
        service.overlayManager.safeAddView(view, params)
    }

    fun hide() {
        panelView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        panelView = null
    }

    private fun bindUi(view: View) {
        val handleDrag = view.findViewById<TextView>(R.id.handleDrag)
        val layoutMainRow = view.findViewById<View>(R.id.layoutMainRow)
        val layoutSubMenu = view.findViewById<View>(R.id.layoutSubMenu)
        val btnSingleBubble = view.findViewById<ImageButton>(R.id.btnSingleBubble)

        val btnPlay = view.findViewById<ImageButton>(R.id.btnPlay)
        val btnAdd = view.findViewById<ImageButton>(R.id.btnAdd)
        val btnCapturePool = view.findViewById<ImageButton>(R.id.btnCapturePool)
        val btnHelpTutorial = view.findViewById<ImageButton>(R.id.btnHelpTutorial)
        val btnToggleMenu = view.findViewById<ImageButton>(R.id.btnToggleMenu)

        val btnClearAll = view.findViewById<ImageButton>(R.id.btnClearAll)
        val btnRecord = view.findViewById<ImageButton>(R.id.btnRecord)
        val btnToggleJoystick = view.findViewById<ImageButton>(R.id.btnToggleJoystick)
        val btnLoadScript = view.findViewById<ImageButton>(R.id.btnLoadScript)
        val btnHideNumbers = view.findViewById<ImageButton>(R.id.btnHideNumbers)
        val btnClose = view.findViewById<ImageButton>(R.id.btnClose)

        var initX = 0
        var initY = 0
        var touchX = 0f
        var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val params = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = params.x
                    initY = params.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dm = service.resources.displayMetrics
                    val maxX = dm.widthPixels - view.width
                    val maxY = dm.heightPixels - view.height
                    params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxY)
                    service.overlayManager.safeUpdateViewLayout(view, params)
                    true
                }
                else -> false
            }
        }

        fun updatePanelState(state: Int) {
            panelState = state % 3
            when (panelState) {
                0 -> {
                    layoutMainRow?.visibility = View.VISIBLE
                    layoutSubMenu?.visibility = View.GONE
                    btnSingleBubble?.visibility = View.GONE
                }
                1 -> {
                    layoutMainRow?.visibility = View.VISIBLE
                    layoutSubMenu?.visibility = View.VISIBLE
                    btnSingleBubble?.visibility = View.GONE
                }
                2 -> {
                    layoutMainRow?.visibility = View.GONE
                    layoutSubMenu?.visibility = View.GONE
                    btnSingleBubble?.visibility = View.VISIBLE
                }
            }
            view.requestLayout()
            val params = view.layoutParams as? WindowManager.LayoutParams
            if (params != null) {
                params.width = WindowManager.LayoutParams.WRAP_CONTENT
                params.height = WindowManager.LayoutParams.WRAP_CONTENT
                service.overlayManager.safeUpdateViewLayout(view, params)
            }
        }

        btnToggleMenu?.setOnClickListener {
            service.vibrateFeedback(20L)
            updatePanelState(panelState + 1)
        }

        btnSingleBubble?.setOnClickListener {
            service.vibrateFeedback(20L)
            updatePanelState(0)
        }

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (service.isPlaying) {
                btnPlay.setImageResource(R.drawable.ic_play)
                service.stopExecutionLoop()
            } else {
                btnPlay.setImageResource(R.drawable.ic_pause)
                service.startScript("default")
            }
        }

        btnAdd?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showAddActionMenu()
        }

        btnCapturePool?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.captureFrameOverlay.show()
        }

        btnHelpTutorial?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showTutorialCard()
        }

        btnClearAll?.setOnClickListener {
            service.vibrateFeedback(30L)
            service.clearAllActions()
        }

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.isRecording) {
                service.stopOverlayRecording()
            } else {
                service.startOverlayRecording()
            }
        }

        btnToggleJoystick?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.joystickOverlay.rootView != null) {
                service.joystickOverlay.hide()
            } else {
                service.joystickOverlay.show()
            }
        }

        btnLoadScript?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showScriptsDialog()
        }

        btnHideNumbers?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.toggleNumbersVisibility()
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.hideControlPanel(openMainApp = true)
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
        }

        val handleDrag = view.findViewById<TextView>(R.id.handleDragStop)
        var initX = 0
        var initY = 0
        var touchX = 0f
        var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val p = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x
                    initY = p.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dm = service.resources.displayMetrics
                    val maxX = dm.widthPixels - view.width
                    val maxY = dm.heightPixels - view.height
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxY)
                    service.overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.stopExecutionLoop()
        }

        service.overlayManager.safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_beacon_ring, null)

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.animate()
            .alpha(0f)
            .setDuration(300)
            .withEndAction {
                service.overlayManager.safeRemoveView(view)
            }
            .start()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt", control_panel_code)

    print("✨ Ошибки ControlPanelOverlay успешно исправлены!")

if __name__ == "__main__":
    apply_control_panel_fix()