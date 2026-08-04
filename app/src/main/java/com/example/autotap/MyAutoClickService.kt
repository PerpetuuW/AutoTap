package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
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

    var isNumbersHidden = false

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

    // CORE MODULES (PUBLIC)
    lateinit var overlayManager: OverlayManager
    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // UI OVERLAYS (PUBLIC)
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay

    // SCRIPT STATE
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false

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

        Toast.makeText(this, "AutoTap v28.15.0 PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun vibrateFeedback(durationMs: Long = 25L) {
        gestureExecutor.vibrateFeedback(durationMs)
    }

    fun showControlPanel() {
        controlPanelOverlay.show()
    }

    fun hideControlPanel() {
        controlPanelOverlay.hide()
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

    fun stopOverlayRecording() {
        isRecording = false
        controlPanelOverlay.show()
        hideFloatingStopButton()
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
