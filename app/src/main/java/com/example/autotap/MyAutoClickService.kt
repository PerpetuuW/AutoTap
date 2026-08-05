package com.example.autotap
import com.example.autotap.*

import android.accessibilityservice.AccessibilityService
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Rect
import android.graphics.Typeface
import android.os.Handler
import android.os.Looper
import android.view.ContextThemeWrapper
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
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.ScriptsDialog
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.io.PrintWriter
import java.lang.ref.WeakReference
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executor
import java.util.concurrent.Executors
import kotlin.math.abs
import kotlin.math.hypot

@Suppress("SpellCheckingInspection", "AccessibilityPolicy", "DEPRECATION", "ClickableViewAccessibility")
@SuppressLint("InflateParams", "SetTextI18n")
class MyAutoClickService : AccessibilityService() {

    val templateRepository by lazy { TemplateRepository(this) }
    val scriptRepository by lazy { ScriptRepository(this, templateRepository) }
    val overlayManager by lazy { OverlayManager(this) }
    val gestureExecutor by lazy { GestureExecutor(this) }

    val controlPanelOverlay by lazy { ControlPanelOverlay(this) }
    val captureFrameOverlay by lazy { CaptureFrameOverlay(this) }
    val joystickOverlay by lazy { JoystickOverlay(this) }
    val editActionDialog by lazy { EditActionDialog(this) }
    val scriptsDialog by lazy { ScriptsDialog(this) }

    val scriptExecutor by lazy { ScriptExecutor(this) }
    val aiScannerEngine by lazy { AiScannerEngine(this) }

    var controlPanelView: View?
        get() = controlPanelOverlay.controlPanelView
        set(value) { controlPanelOverlay.controlPanelView = value }

    var floatingStopView: View? = null
    var candidateSelectionOverlayView: View? = null
    var recordOverlayView: View? = null
    var recordBarView: View? = null
    var visualizerOverlay: View? = null

    var tutorialCardView: View? = null
    var currentTutorialStep = 0
    var isTutorialActive = false

    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false

    val globalTemplates: ArrayList<Bitmap> get() = templateRepository.globalTemplates
    val globalTemplatesNames: ArrayList<String> get() = templateRepository.globalTemplatesNames

    var isNumbersHidden = false
    var isRecording = false
    var isInjectingGesture = false
    var lastRecordedTime = 0L

    var globalClickDurationMs: Long = 120L
    var globalSwipeDurationMs: Long = 300L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = true
    var globalRelayNextScript: String = ""

    val uiExecutor = Executor { command ->
        Handler(Looper.getMainLooper()).post(command)
    }

    val bgScannerExecutor = Executors.newSingleThreadExecutor()

    companion object {
        private var serviceRef: WeakReference<MyAutoClickService>? = null
        private val logLock = Any()

        @JvmStatic
        var instance: MyAutoClickService?
            get() = serviceRef?.get()
            set(value) {
                serviceRef = if (value != null) WeakReference(value) else null
            }

        @JvmStatic
        fun logError(context: Context, e: Throwable) {
            android.util.Log.e("AutoTap", "Caught Exception", e)
            synchronized(logLock) {
                try {
                    val logFile = File(context.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("=== ${sdf.format(Date())} ===")
                        e.printStackTrace(writer)
                        writer.println()
                        writer.flush()
                    }
                } catch (_: Exception) {}
            }
        }

        @JvmStatic
        fun logAppEvent(context: Context, tag: String, message: String) {
            // Рабочие отладочные сообщения пишутся в системный Logcat, не засоряя error_log.txt
            android.util.Log.d("AutoTap", "[$tag] $message")
        }
    }

    fun isOverlayArea(x: Int, y: Int): Boolean {
        val overlays = listOf(
            joystickOverlay.joystickOverlayView,
            controlPanelView,
            recordBarView,
            floatingStopView
        )
        for (v in overlays) {
            if (v != null && v.visibility == View.VISIBLE) {
                val loc = IntArray(2)
                v.getLocationOnScreen(loc)
                val rect = Rect(loc[0], loc[1], loc[0] + v.width, loc[1] + v.height)
                if (rect.contains(x, y)) return true
            }
        }
        return false
    }

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) = overlayManager.safeAddView(view, params)
    fun safeRemoveView(view: View?) = overlayManager.safeRemoveView(view)
    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) = overlayManager.safeUpdateViewLayout(view, params)
    fun dpToPx(dp: Int): Int = overlayManager.dpToPx(dp)
    fun dpToPx(dp: Float): Int = overlayManager.dpToPx(dp)

    fun loadAllTemplatesFromDisk() = templateRepository.loadAllTemplatesFromDisk()
    fun loadTemplateMetadata(maskPath: String) = templateRepository.loadTemplateMetadata(maskPath)
    fun moveTemplateToTrash(index: Int) = templateRepository.moveTemplateToTrash(index)
    fun exportScriptWithTemplates(context: Context, scriptName: String) = scriptRepository.exportScriptWithTemplates(context, scriptName)
    fun vibrateFeedback(durationMs: Long = 25L) = gestureExecutor.vibrateFeedback(durationMs)

    fun showControlPanel() = controlPanelOverlay.show()
    fun hideControlPanel(openMainApp: Boolean = false) = controlPanelOverlay.hide(openMainApp)
    fun showCaptureFrame() = captureFrameOverlay.show()
    fun showJoystickManipulator() = joystickOverlay.show()
    fun showEditDialog(config: ActionConfig) = editActionDialog.show(config)
    fun showScriptsDialog() = scriptsDialog.show()

    fun startExecutionLoop() = scriptExecutor.startExecutionLoop()
    fun stopExecutionLoop() = scriptExecutor.stopExecutionLoop()
    fun startTemplateCalibration(config: ActionConfig) = aiScannerEngine.startTemplateCalibration(config)

    fun computeFastBitmapHash(bitmap: Bitmap): Int {
        val w = bitmap.width; val h = bitmap.height
        if (w <= 0 || h <= 0) return 0
        var hash = 17
        val sampleStepX = (w / 12).coerceAtLeast(1)
        val sampleStepY = (h / 12).coerceAtLeast(1)
        for (y in 0 until h step sampleStepY) {
            for (x in 0 until w step sampleStepX) {
                hash = 31 * hash + bitmap.getPixel(x, y)
            }
        }
        return hash
    }

    fun showClickVisualizer(x: Float, y: Float) {
        uiExecutor.execute {
            if (visualizerOverlay == null) {
                visualizerOverlay = View(this).apply { background = getDrawable(R.drawable.circle_target) }
                val params = WindowManager.LayoutParams(
                    overlayManager.dpToPx(40), overlayManager.dpToPx(40), overlayManager.getOverlayType(),
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                    PixelFormat.TRANSLUCENT
                )
                overlayManager.safeAddView(visualizerOverlay, params)
            }

            val params = visualizerOverlay?.layoutParams as? WindowManager.LayoutParams
            if (params != null) {
                params.x = (x - overlayManager.dpToPx(20)).toInt()
                params.y = (y - overlayManager.dpToPx(20)).toInt()
                overlayManager.safeUpdateViewLayout(visualizerOverlay, params)

                visualizerOverlay?.alpha = 1f
                visualizerOverlay?.scaleX = 0.5f; visualizerOverlay?.scaleY = 0.5f
                visualizerOverlay?.animate()?.scaleX(2.0f)?.scaleY(2.0f)?.alpha(0f)?.setDuration(300)?.start()
            }
        }
    }

    fun showScriptPickerDialog(titleText: String, onScriptSelected: (String) -> Unit) {
        val dir = File(filesDir, "scripts")
        val scriptFiles = dir.listFiles()?.filter { it.name.endsWith(".json") } ?: emptyList()

        val dialogView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#161B22"))
            setPadding(overlayManager.dpToPx(14), overlayManager.dpToPx(14), overlayManager.dpToPx(14), overlayManager.dpToPx(14))
        }

        val tvTitle = TextView(this).apply {
            text = titleText; setTextColor(Color.WHITE); textSize = 14f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, 0, 0, overlayManager.dpToPx(10))
        }
        dialogView.addView(tvTitle)

        val listLayout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }

        val btnNone = Button(this).apply {
            text = "❌ Нет / Очистить"; setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.parseColor("#21262D"))
            textSize = 11f
            setOnClickListener { overlayManager.safeRemoveView(dialogView); onScriptSelected("") }
        }
        listLayout.addView(btnNone)

        for (file in scriptFiles) {
            val name = file.nameWithoutExtension
            val btnSc = Button(this).apply {
                text = "📁 $name"; setTextColor(Color.WHITE)
                backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
                textSize = 11f
                setOnClickListener { overlayManager.safeRemoveView(dialogView); onScriptSelected(name) }
            }
            listLayout.addView(btnSc)
        }

        val scroll = android.widget.ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, overlayManager.dpToPx(220))
            addView(listLayout)
        }
        dialogView.addView(scroll)

        val btnClose = Button(this).apply {
            text = "Отмена"
            backgroundTintList = ColorStateList.valueOf(Color.parseColor("#F04438"))
            setOnClickListener { overlayManager.safeRemoveView(dialogView) }
        }
        dialogView.addView(btnClose)

        val params = WindowManager.LayoutParams(
            overlayManager.dpToPx(280), WindowManager.LayoutParams.WRAP_CONTENT,
            overlayManager.getOverlayType(), WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.CENTER }

        overlayManager.safeAddView(dialogView, params)
    }

    fun showAddActionMenu() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            overlayManager.getOverlayType(), WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.CENTER }

        val btnClick = dialogView.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = dialogView.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = dialogView.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelAdd)

        val spawnOffset = (actionsList.size % 8) * overlayManager.dpToPx(24).toFloat()
        val spawnX = 350f + spawnOffset; val spawnY = 350f + spawnOffset

        btnClick?.setOnClickListener {
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1)
            overlayManager.safeRemoveView(dialogView)
        }
        btnSwipe?.setOnClickListener {
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1)
            spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f)
            overlayManager.safeRemoveView(dialogView)
        }
        btnAi?.setOnClickListener {
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0)
            overlayManager.safeRemoveView(dialogView)
        }
        btnCancel?.setOnClickListener { overlayManager.safeRemoveView(dialogView) }
        overlayManager.safeAddView(dialogView, params)
    }

    fun startOverlayRecording() {
        isRecording = true
        isInjectingGesture = false
        lastRecordedTime = System.currentTimeMillis()

        actionsList.forEach { act -> act.startView.visibility = View.INVISIBLE; act.endView?.visibility = View.INVISIBLE }
        controlPanelView?.visibility = View.GONE
        showFloatingStopButton()

        if (recordOverlayView == null) {
            recordOverlayView = View(this).apply { setBackgroundColor(0x01000000) }
        }

        val overlayParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT,
            overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        )

        var downX = 0f; var downY = 0f; var downTime = 0L

        recordOverlayView?.setOnTouchListener { v, event ->
            if (!isRecording || isInjectingGesture) return@setOnTouchListener false
            val x = event.rawX; val y = event.rawY

            if (isOverlayArea(x.toInt(), y.toInt())) {
                logAppEvent(this, "SKIP_RECORD_TOUCH", "Игнорируем нажатие по overlay: ($x, $y)")
                return@setOnTouchListener false
            }

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = x; downY = y; downTime = System.currentTimeMillis()
                    return@setOnTouchListener true
                }
                MotionEvent.ACTION_UP -> {
                    v.performClick()
                    val upTime = System.currentTimeMillis()
                    val dist = hypot((x - downX).toDouble(), (y - downY).toDouble())
                    val delay = (downTime - lastRecordedTime).coerceIn(80L, 5000L)
                    val gestureHoldDuration = (upTime - downTime).coerceIn(80L, 3000L)
                    lastRecordedTime = downTime

                    isInjectingGesture = true
                    overlayManager.safeRemoveView(recordOverlayView)

                    Handler(Looper.getMainLooper()).postDelayed({
                        if (dist > 60) {
                            addNewActionAtPosition(downX, downY, delay, ActionType.SWIPE, -1)
                            val currentConfig = actionsList.last()
                            currentConfig.holdDuration = gestureHoldDuration
                            spawnEndTargetAtPosition(currentConfig, x, y)
                            gestureExecutor.performSwipeWithCallback(downX, downY, x, y, duration = gestureHoldDuration) {
                                Handler(Looper.getMainLooper()).post {
                                    overlayManager.safeAddView(recordOverlayView, overlayParams)
                                    isInjectingGesture = false
                                }
                            }
                        } else {
                            addNewActionAtPosition(downX, downY, delay, ActionType.CLICK, -1)
                            gestureExecutor.performClickWithCallback(downX, downY, duration = 100L) {
                                Handler(Looper.getMainLooper()).post {
                                    overlayManager.safeAddView(recordOverlayView, overlayParams)
                                    isInjectingGesture = false
                                }
                            }
                        }
                    }, 25L)
                    return@setOnTouchListener true
                }
            }
            false
        }

        overlayManager.safeAddView(recordOverlayView, overlayParams)
        showRecordBar()
    }

    fun stopOverlayRecording() {
        isRecording = false; isInjectingGesture = false
        if (recordOverlayView != null) { overlayManager.safeRemoveView(recordOverlayView); recordOverlayView = null }
        if (recordBarView != null) { overlayManager.safeRemoveView(recordBarView); recordBarView = null }
        hideFloatingStopButton()
        controlPanelView?.visibility = View.VISIBLE
        actionsList.forEach { act ->
            act.startView.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    private fun showRecordBar() {
        if (recordBarView != null) return
        val btnStop = Button(this).apply {
            text = "⏹ СТОП ЗАПИСИ"; setTextColor(Color.WHITE)
            textSize = 13f; setTypeface(null, Typeface.BOLD)
            backgroundTintList = ColorStateList.valueOf(getColor(R.color.red_close))
            setPadding(overlayManager.dpToPx(16), overlayManager.dpToPx(8), overlayManager.dpToPx(16), overlayManager.dpToPx(8))
        }
        val barParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL; y = overlayManager.dpToPx(40) }

        btnStop.setOnClickListener { vibrateFeedback(30L); stopOverlayRecording() }
        recordBarView = btnStop
        overlayManager.safeAddView(recordBarView, barParams)
    }

    fun showTutorialCard() {
        if (!isTutorialActive) return
        if (tutorialCardView != null) { tutorialCardView?.visibility = View.VISIBLE; return }

        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        tutorialCardView = LayoutInflater.from(contextThemeWrapper).inflate(R.layout.floating_tutorial_card, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            overlayManager.getOverlayType(), WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        )

        val btnSkip = tutorialCardView!!.findViewById<Button>(R.id.btnTutSkip)
        btnSkip?.setOnClickListener {
            vibrateFeedback(20L); isTutorialActive = false
            overlayManager.safeRemoveView(tutorialCardView); tutorialCardView = null
        }

        overlayManager.safeAddView(tutorialCardView, params)
    }

    fun removeCandidateSelectionOverlay() {
        if (candidateSelectionOverlayView != null) {
            overlayManager.safeRemoveView(candidateSelectionOverlayView)
            candidateSelectionOverlayView = null
        }
    }

    fun addNewActionAtPosition(posX: Float, posY: Float, recordedDelay: Long, actionType: ActionType, templateIndex: Int) {
        val actionId = actionsList.size + 1
        val startView = LayoutInflater.from(this).inflate(R.layout.floating_target, null)
        val tvNum = startView.findViewById<TextView>(R.id.tvTargetNumber)
        tvNum?.text = actionId.toString()

        val sizePx = overlayManager.dpToPx(36)
        val params = WindowManager.LayoutParams(
            sizePx, sizePx, overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.TOP or Gravity.START; x = (posX - sizePx / 2f).toInt(); y = (posY - sizePx / 2f).toInt() }

        val config = ActionConfig(id = actionId, startView = startView, type = actionType, delay = recordedDelay, selectedTemplateIndex = templateIndex)

        startView.setOnTouchListener(object : View.OnTouchListener {
            private var initialX = 0; private var initialY = 0
            private var initialTouchX = 0f; private var initialTouchY = 0f
            private var isMoving = false

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = params.x; initialY = params.y
                        initialTouchX = event.rawX; initialTouchY = event.rawY
                        isMoving = false; return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = abs(event.rawX - initialTouchX); val dy = abs(event.rawY - initialTouchY)
                        if (dx > 8 || dy > 8) {
                            isMoving = true
                            val displayMetrics = resources.displayMetrics
                            params.x = (initialX + (event.rawX - initialTouchX).toInt()).coerceIn(0, displayMetrics.widthPixels - sizePx)
                            params.y = (initialY + (event.rawY - initialTouchY).toInt()).coerceIn(0, displayMetrics.heightPixels - sizePx)
                            overlayManager.safeUpdateViewLayout(startView, params)
                        }
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        if (!isMoving && !isPlaying) {
                            vibrateFeedback(25L)
                            showEditDialog(config)
                        }
                        return true
                    }
                }
                return false
            }
        })

        if (isRecording) {
            startView.visibility = View.INVISIBLE
        }

        actionsList.add(config)
        overlayManager.safeAddView(startView, params)
    }

    fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = overlayManager.dpToPx(36)
        val params = WindowManager.LayoutParams(
            sizePx, sizePx, overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.TOP or Gravity.START; x = (posX - sizePx / 2f).toInt(); y = (posY - sizePx / 2f).toInt() }

        if (isRecording) {
            endView.visibility = View.INVISIBLE
        }

        config.endView = endView
        overlayManager.safeAddView(endView, params)
    }

    fun setTargetsTouchable(touchable: Boolean) {
        for (action in actionsList) {
            val params = action.startView.layoutParams as? WindowManager.LayoutParams ?: continue
            if (touchable) params.flags = params.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
            else params.flags = params.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
            overlayManager.safeUpdateViewLayout(action.startView, params)
        }
    }

    fun showFloatingStopButton() {
        if (floatingStopView != null) { floatingStopView?.visibility = View.VISIBLE; return }
        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        floatingStopView = LayoutInflater.from(contextThemeWrapper).inflate(R.layout.floating_stop_button, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            overlayManager.getOverlayType(), WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.TOP or Gravity.START; x = 100; y = 200 }

        floatingStopView!!.findViewById<View>(R.id.btnFloatingStop)?.setOnClickListener {
            vibrateFeedback(30L); stopExecutionLoop()
        }
        overlayManager.safeAddView(floatingStopView, params)
    }

    fun hideFloatingStopButton() {
        if (floatingStopView != null) { overlayManager.safeRemoveView(floatingStopView); floatingStopView = null }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        loadAllTemplatesFromDisk()
    }

    override fun onUnbind(intent: Intent?): Boolean { instance = null; return super.onUnbind(intent) }

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel(false)
        instance = null
        bgScannerExecutor.shutdown()
        super.onDestroy()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}

    fun findTemplateMatchForIndex(screenBitmap: Bitmap?, action: ActionConfig, templateIdx: Int): MatchCandidate? {
        if (screenBitmap == null) return null
        if (templateIdx !in globalTemplates.indices) return null
        val templatePath = globalTemplatesNames[templateIdx]
        val template = globalTemplates[templateIdx]
        val meta = templateRepository.loadTemplateMetadata(templatePath)

        val savedPct = meta?.optInt("similarityPercent", 70) ?: 70
        val targetThreshold = (savedPct / 100f).coerceIn(0.10f, 0.99f)

        val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(screenBitmap, template, meta, action)
        if (candidates.isEmpty()) return null

        val best = candidates.first()
        if (best.score >= targetThreshold) return best
        return null
    }

    fun loadScriptByName(name: String) {
        try {
            val dir = File(filesDir, "scripts")
            val scriptFile = File(dir, "$name.json")
            if (!scriptFile.exists()) return

            val jsonArray = JSONArray(scriptFile.readText())
            uiExecutor.execute {
                actionsList.forEach { act ->
                    overlayManager.safeRemoveView(act.startView)
                    act.endView?.let { safeRemoveView(it) }
                }
                actionsList.clear()

                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    val typeStr = obj.optString("type", "CLICK")
                    val type = try { ActionType.valueOf(typeStr) } catch (e: Exception) { ActionType.CLICK }
                    val x = obj.optInt("x", 500).toFloat(); val y = obj.optInt("y", 500).toFloat()
                    val delay = obj.optLong("delay", 1000L)
                    val act = addNewActionAtPosition(x, y, delay, type, obj.optInt("selectedTemplateIndex", -1))

                    act.repeatCount = obj.optInt("repeatCount", 1)
                    act.holdDuration = obj.optLong("holdDuration", 1000L)
                    act.randomRadius = obj.optInt("randomRadius", 0)

                    act.playAudioOnMatch = obj.optBoolean("playAudioOnMatch", false)
                    act.clickAiTarget = obj.optBoolean("clickAiTarget", false)
                    act.aiTimeoutSeconds = obj.optInt("aiTimeoutSeconds", 15)
                    act.similarityPercent = obj.optInt("similarityPercent", 70)
                    act.scanIntervalSeconds = obj.optInt("scanIntervalSeconds", 5)
                    act.postMatchDelaySeconds = obj.optInt("postMatchDelaySeconds", 3)
                    act.jumpToStepOnMatch = obj.optInt("jumpToStepOnMatch", -1)
                    act.targetScriptToLoad = obj.optString("targetScriptToLoad", "")
                    act.isFastMode = obj.optBoolean("isFastMode", false)

                    act.endX = obj.optInt("endX", 0)
                    act.endY = obj.optInt("endY", 0)

                    val jpArr = obj.optJSONArray("joystickPath") ?: JSONArray()
                    act.joystickPath.clear()
                    for (j in 0 until jpArr.length()) {
                        val p = jpArr.optJSONObject(j)
                        if (p != null) {
                            act.joystickPath.add(android.graphics.PointF(
                                p.optDouble("x", 0.0).toFloat(),
                                p.optDouble("y", 0.0).toFloat()
                            ))
                        }
                    }

                    act.multiScaleSearch = obj.optBoolean("multiScaleSearch", false)
                    act.shapeOnlyMode = obj.optBoolean("shapeOnlyMode", false)

                    act.searchAreaX = obj.optInt("searchAreaX", 0)
                    act.searchAreaY = obj.optInt("searchAreaY", 0)
                    act.searchAreaW = obj.optInt("searchAreaW", 0)
                    act.searchAreaH = obj.optInt("searchAreaH", 0)
                }
            }
        } catch (e: Exception) { logError(this, e) }
    }
}