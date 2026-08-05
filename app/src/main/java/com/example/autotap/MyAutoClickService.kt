package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.accessibilityservice.GestureDescription
import android.animation.ObjectAnimator
import android.animation.PropertyValuesHolder
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
import android.view.Display
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
import java.io.PrintWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.math.abs

class MyAutoClickService : AccessibilityService() {

    companion object {
        var instance: MyAutoClickService? = null
        private val logLock = Any()

        @JvmStatic
        fun logError(ctx: Context, e: Throwable) {
            android.util.Log.e("AutoTap", "Caught Exception", e)
            synchronized(logLock) {
                try {
                    val logFile = File(ctx.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("=== [${sdf.format(Date())}] [ERROR] ===")
                        e.printStackTrace(writer)
                        writer.println()
                        writer.flush()
                    }
                } catch (_: Exception) {}
            }
        }

        @JvmStatic
        fun logAppEvent(ctx: Context, tag: String, msg: String) {
            android.util.Log.d("AutoTap", "[$tag] $msg")
            synchronized(logLock) {
                try {
                    val logFile = File(ctx.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("[${sdf.format(Date())}] [$tag] $msg")
                        writer.flush()
                    }
                } catch (_: Exception) {}
            }
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

    // --- TUTORIAL STATE ---
    private var tutorialCardView: View? = null
    private var currentTutorialStep = 0
    private var isTutorialActive = false
    private var highlightedButtonAnim: ObjectAnimator? = null

    // --- STATE ---
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalSwipeDurationMs: Long = 300L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplates: ArrayList<Bitmap>
        get() = templateRepository.globalTemplates

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    private val uiHandler = Handler(Looper.getMainLooper())
    private val bgScannerExecutor = Executors.newSingleThreadExecutor()

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

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

        logAppEvent(this, "SERVICE", "🚀 Служба AutoTap v37.6.0-PRO успешно подключена к системе")
        Toast.makeText(this, "AutoTap v37.6.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun vibrateFeedback(ms: Long = 25L) = gestureExecutor.vibrateFeedback(ms)

    fun getRealScreenSize(): Pair<Int, Int> = overlayManager.getRealScreenSize()
    fun dpToPx(dp: Int): Int = overlayManager.dpToPx(dp)
    fun dpToPx(dp: Float): Int = overlayManager.dpToPx(dp)

    fun showControlPanel() {
        logAppEvent(this, "OVERLAY", "Показ главной панели управления")
        controlPanelOverlay.show()
    }

    fun hideControlPanel(openMainApp: Boolean = false) {
        hideTutorial()
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
            logAppEvent(this, "SCRIPT", "⚠️ Попытка запуска пустого сценария '$name'")
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        logAppEvent(this, "SCRIPT", "▶️ Запуск сценария '$name' (${actionsList.size} шагов)")
        scenarioRunner.start()
    }

    fun stopExecutionLoop() {
        logAppEvent(this, "SCRIPT", "⏹ Остановка выполнения сценария")
        scenarioRunner.stop()
    }

    fun startOverlayRecording() {
        isRecording = true
        logAppEvent(this, "RECORDING", "🔴 Запуск живой записи жестов по экрану")
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        controlPanelOverlay.hide()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        logAppEvent(this, "RECORDING", "⏹ Запись жестов завершена. Всего записано шагов: ${actionsList.size}")
        controlPanelOverlay.show()
        hideFloatingStopButton()
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    fun toggleNumbersVisibility() {
        isNumbersHidden = !isNumbersHidden
        logAppEvent(this, "UI", "Переключение видимости бейджей: isHidden=$isNumbersHidden")
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
        Toast.makeText(this, if (isNumbersHidden) "👁 Номера скрыты" else "👁 Номера показаны", Toast.LENGTH_SHORT).show()
    }

    fun clearAllActions() {
        logAppEvent(this, "SCRIPT", "🗑 Очистка всех шагов сценария (${actionsList.size} шагов было)")
        actionsList.forEach { act ->
            act.startView?.let { overlayManager.safeRemoveView(it) }
            act.endView?.let { overlayManager.safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(x: Float, y: Float, delay: Long, type: ActionType, id: Int) {
        val actionId = if (id == -1) (actionsList.size + 1) else id
        logAppEvent(this, "STEP_ADD", "Добавлен шаг #$actionId [$type] в ($x, $y) с задержкой ${delay}мс")

        val cfg = ActionConfig(
            id = actionId,
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

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = globalSwipeDurationMs, onComplete: ((Boolean) -> Unit)? = null) {
        gestureExecutor.performSwipeWithCallback(startX, startY, endX, endY, duration, onComplete)
    }

    fun performPathSwipeWithCallback(pathPoints: List<PointF>, startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = globalSwipeDurationMs, onComplete: ((Boolean) -> Unit)? = null) {
        gestureExecutor.performPathSwipeWithCallback(pathPoints, startX, startY, endX, endY, duration, onComplete)
    }

    fun showClickVisualizer(x: Float, y: Float) = clickVisualizerOverlay.showClickAt(x, y)

    fun captureScreenBitmap(): Bitmap? {
        var resultBitmap: Bitmap? = null
        val latch = CountDownLatch(1)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            takeScreenshot(Display.DEFAULT_DISPLAY, bgScannerExecutor, object : TakeScreenshotCallback {
                override fun onSuccess(screenshotResult: ScreenshotResult) {
                    val hwBuffer = screenshotResult.hardwareBuffer
                    try {
                        val hwBitmap = Bitmap.wrapHardwareBuffer(hwBuffer, screenshotResult.colorSpace)
                        resultBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, false)
                    } catch (e: Exception) {
                        logError(this@MyAutoClickService, e)
                    } finally {
                        hwBuffer.close()
                        latch.countDown()
                    }
                }

                override fun onFailure(errorCode: Int) {
                    logAppEvent(this@MyAutoClickService, "SCREENSHOT", "❌ Сбой вызова takeScreenshot с кодом $errorCode")
                    latch.countDown()
                }
            })

            try { latch.await(1500L, java.util.concurrent.TimeUnit.MILLISECONDS) } catch (_: Exception) {}
        }

        if (resultBitmap == null) {
            val (w, h) = getRealScreenSize()
            resultBitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        }

        return resultBitmap
    }

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
        isTutorialActive = true
        if (tutorialCardView != null) {
            tutorialCardView?.visibility = View.VISIBLE
            updateTutorialContent()
            return
        }

        val view = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        tutorialCardView = view

        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
        }

        val btnPrev = view.findViewById<Button>(R.id.btnTutPrev)
        val btnNext = view.findViewById<Button>(R.id.btnTutNext)
        val btnSkip = view.findViewById<Button>(R.id.btnTutSkip)

        btnPrev?.setOnClickListener {
            vibrateFeedback(20L)
            if (currentTutorialStep > 0) {
                currentTutorialStep--
                updateTutorialContent()
            }
        }

        btnNext?.setOnClickListener {
            vibrateFeedback(20L)
            if (currentTutorialStep < 10) {
                currentTutorialStep++
                updateTutorialContent()
            } else {
                hideTutorial()
            }
        }

        btnSkip?.setOnClickListener {
            vibrateFeedback(20L)
            hideTutorial()
        }

        overlayManager.safeAddView(view, params)
        updateTutorialContent()
    }

    private fun updateTutorialContent() {
        if (tutorialCardView == null) return

        if (currentTutorialStep >= 5) {
            controlPanelOverlay.ensureSubMenuVisible()
        }

        val targetButton: View? = controlPanelOverlay.getButtonForStep(currentTutorialStep)
        highlightButton(targetButton)

        uiHandler.post {
            positionTutorialCardAnchored(targetButton)
        }

        val tvTitle = tutorialCardView?.findViewById<TextView>(R.id.tvTutTitle)
        val tvDesc = tutorialCardView?.findViewById<TextView>(R.id.tvTutDesc)
        val btnNext = tutorialCardView?.findViewById<Button>(R.id.btnTutNext)

        when (currentTutorialStep) {
            0 -> {
                tvTitle?.text = "1/11: Запуск [▶]"
                tvDesc?.text = "Запускает и останавливает выполнение всех созданных шагов."
                btnNext?.text = "Далее ►"
            }
            1 -> {
                tvTitle?.text = "2/11: Добавить [+]"
                tvDesc?.text = "Добавляет новый обычный клик, свайп или ИИ-триггер."
                btnNext?.text = "Далее ►"
            }
            2 -> {
                tvTitle?.text = "3/11: ИИ-Сканер [📸]"
                tvDesc?.text = "Открывает прицел для вырезания картинки с экрана и создания ИИ-маски."
                btnNext?.text = "Далее ►"
            }
            3 -> {
                tvTitle?.text = "4/11: Справка [❓]"
                tvDesc?.text = "Повторный вызов этого интерактивного обучения по кнопкам."
                btnNext?.text = "Далее ►"
            }
            4 -> {
                tvTitle?.text = "5/11: Меню [☰]"
                tvDesc?.text = "Разворачивает и сворачивает дополнительную панель инструментов."
                btnNext?.text = "Далее ►"
            }
            5 -> {
                tvTitle?.text = "6/11: Очистить [🗑]"
                tvDesc?.text = "Удаляет абсолютно все мишени и шаги с экрана."
                btnNext?.text = "Далее ►"
            }
            6 -> {
                tvTitle?.text = "7/11: Запись [🔴]"
                tvDesc?.text = "Включает живую запись ваших кликов и свайпов прямо по экрану!"
                btnNext?.text = "Далее ►"
            }
            7 -> {
                tvTitle?.text = "8/11: Джойстик [🕹]"
                tvDesc?.text = "Включает плавающий джойстик для записи жестов свайпа."
                btnNext?.text = "Далее ►"
            }
            8 -> {
                tvTitle?.text = "9/11: Скрипты [📁]"
                tvDesc?.text = "Сохранение текущей схемы шагов в файл и загрузка сохраненных."
                btnNext?.text = "Далее ►"
            }
            9 -> {
                tvTitle?.text = "10/11: Глаз [👁]"
                tvDesc?.text = "Скрывает или показывает бейджи с номерами поверх шагов."
                btnNext?.text = "Далее ►"
            }
            10 -> {
                tvTitle?.text = "11/11: Закрыть [❌]"
                tvDesc?.text = "Выход из панели кликера и возвращение в главное меню."
                btnNext?.text = "Завершить ✔"
            }
        }
    }

    private fun positionTutorialCardAnchored(targetButton: View?) {
        val card = tutorialCardView ?: return
        val panel = controlPanelOverlay.rootView ?: return

        val (screenW, screenH) = overlayManager.getRealScreenSize()
        val loc = IntArray(2)
        if (targetButton != null && targetButton.width > 0) {
            targetButton.getLocationOnScreen(loc)
        } else {
            panel.getLocationOnScreen(loc)
        }

        val anchorX = loc[0]
        val anchorY = loc[1]

        val cardW = dpToPx(240)
        val cardH = dpToPx(150)
        val margin = dpToPx(12)

        var cardX = anchorX + dpToPx(50)
        var cardY = anchorY + dpToPx(50)

        if (cardX + cardW > screenW - margin) {
            cardX = anchorX - cardW - margin
        }
        if (cardY + cardH > screenH - margin) {
            cardY = anchorY - cardH - margin
        }

        cardX = cardX.coerceIn(margin, (screenW - cardW - margin).coerceAtLeast(margin))
        cardY = cardY.coerceIn(dpToPx(60), (screenH - cardH - margin).coerceAtLeast(dpToPx(60)))

        val params = card.layoutParams as? WindowManager.LayoutParams ?: return
        params.gravity = Gravity.TOP or Gravity.START
        params.x = cardX
        params.y = cardY
        overlayManager.safeUpdateViewLayout(card, params)
    }

    private fun highlightButton(button: View?) {
        clearButtonHighlights()
        if (button == null) return

        highlightedButtonAnim = ObjectAnimator.ofPropertyValuesHolder(
            button,
            PropertyValuesHolder.ofFloat(View.SCALE_X, 1.0f, 1.25f, 1.0f),
            PropertyValuesHolder.ofFloat(View.SCALE_Y, 1.0f, 1.25f, 1.0f)
        ).apply {
            duration = 600
            repeatCount = ObjectAnimator.INFINITE
            start()
        }
    }

    private fun clearButtonHighlights() {
        highlightedButtonAnim?.cancel()
        highlightedButtonAnim = null
        controlPanelOverlay.resetAllButtonScales()
    }

    fun hideTutorial() {
        clearButtonHighlights()
        isTutorialActive = false
        tutorialCardView?.let {
            overlayManager.safeRemoveView(it)
            tutorialCardView = null
        }
    }

    fun loadScriptByName(name: String): List<ActionConfig> = scriptRepository.loadScriptByName(name)
    fun saveScriptByName(name: String, actions: List<ActionConfig>) = scriptRepository.saveScriptByName(name, actions)

    fun loadAllTemplatesFromDisk() = templateRepository.loadAllTemplatesFromDisk()
    fun moveTemplateToTrash(index: Int) = templateRepository.moveTemplateToTrash(index)
    fun exportScriptWithTemplates(context: Context, scriptName: String) = scriptRepository.exportScriptWithTemplates(scriptName)

    override fun onDestroy() {
        logAppEvent(this, "SERVICE", "🛑 Служба AutoTap остановлена")
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        bgScannerExecutor.shutdown()
        super.onDestroy()
    }
}
