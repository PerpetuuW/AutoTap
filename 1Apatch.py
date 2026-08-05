import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан файл: {rel_path}")

def fix_joystick_recording():
    print("🚀 Восстановление и реставрация записи джойстика v35.3.0-PRO...")

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
        versionCode = 2375
        versionName = "35.3.0-PRO"

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

    # 2. MyAutoClickService.kt (Полная реализация джойстика и многоточечных свайпов)
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.*
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.util.DisplayMetrics
import android.view.*
import android.view.accessibility.AccessibilityEvent
import android.widget.*
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.*
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.min

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

    private lateinit var windowManager: WindowManager
    private val attachedViews = ConcurrentHashMap<View, Boolean>()
    private val uiHandler = Handler(Looper.getMainLooper())
    private val bgScannerExecutor = Executors.newSingleThreadExecutor()

    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalSwipeDurationMs: Long = 300L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplates = ArrayList<Bitmap>()
    val globalTemplatesNames = ArrayList<String>()

    private var controlPanelView: View? = null
    private var stopButtonView: View? = null
    private var captureFrameView: View? = null
    private var joystickOverlayView: View? = null

    private var executionThread: Thread? = null

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v35.3.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun dpToPx(dp: Int): Int = (dp * resources.displayMetrics.density).toInt()
    fun dpToPx(dp: Float): Int = (dp * resources.displayMetrics.density).toInt()

    fun getRealScreenSize(): Pair<Int, Int> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val bounds = windowManager.currentWindowMetrics.bounds
            Pair(bounds.width(), bounds.height())
        } else {
            val dm = DisplayMetrics()
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay.getRealMetrics(dm)
            Pair(dm.widthPixels, dm.heightPixels)
        }
    }

    fun getOverlayType(): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
    }

    fun createOverlayParams(): WindowManager.LayoutParams {
        return WindowManager.LayoutParams().apply {
            type = getOverlayType()
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }

            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }
    }

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] == true) return
        try {
            windowManager.addView(view, params)
            attachedViews[view] = true
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun safeRemoveView(view: View?) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            logError(this, e)
        } finally {
            attachedViews.remove(view)
        }
    }

    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.updateViewLayout(view, params)
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun vibrateFeedback(durationMs: Long = 25L) {
        try {
            val vibrator = getSystemService(VIBRATOR_SERVICE) as? Vibrator
            if (vibrator != null && vibrator.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (_: Exception) {}
    }

    fun normalizeX(px: Float): Float {
        val (w, _) = getRealScreenSize()
        return (px / w.toFloat()).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val (_, h) = getRealScreenSize()
        return (px / h.toFloat()).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val (w, h) = getRealScreenSize()
        return Pair((nx * w).coerceIn(0f, w.toFloat()), (ny * h).coerceIn(0f, h.toFloat()))
    }

    fun randomOffset(radius: Int): PointF {
        if (radius <= 0) return PointF(0f, 0f)
        val dx = (-radius..radius).random().toFloat()
        val dy = (-radius..radius).random().toFloat()
        return PointF(dx, dy)
    }

    fun captureScreenBitmap(): Bitmap? {
        return try {
            val (w, h) = getRealScreenSize()
            Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            logError(this, e)
            null
        }
    }

    fun performClickWithCallback(x: Float, y: Float, duration: Long = 100L, onComplete: ((Boolean) -> Unit)? = null) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }
        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                onComplete?.invoke(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                onComplete?.invoke(false)
            }
        }, null)
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        performPathSwipeWithCallback(emptyList(), startX, startY, endX, endY, duration, onComplete)
    }

    fun performPathSwipeWithCallback(
        pathPoints: List<PointF>,
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        duration: Long = 300L,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }
        val path = Path().apply {
            if (pathPoints.size >= 2) {
                moveTo(pathPoints.first().x, pathPoints.first().y)
                for (i in 1 until pathPoints.size) {
                    lineTo(pathPoints[i].x, pathPoints[i].y)
                }
            } else {
                moveTo(startX, startY)
                lineTo(endX, endY)
            }
        }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                onComplete?.invoke(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                onComplete?.invoke(false)
            }
        }, null)
    }

    fun showControlPanel() {
        if (controlPanelView != null) {
            controlPanelView?.visibility = View.VISIBLE
            return
        }

        val view = LayoutInflater.from(this).inflate(R.layout.floating_control_panel, null)
        controlPanelView = view

        val params = createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = dpToPx(20)
            y = dpToPx(120)
        }

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
                    val (screenW, screenH) = getRealScreenSize()
                    val w = if (view.width > 0) view.width else dpToPx(180)
                    val h = if (view.height > 0) view.height else dpToPx(50)
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (screenW - w).coerceAtLeast(0))
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (screenH - h).coerceAtLeast(0))
                    safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        var panelState = 0
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
            val p = view.layoutParams as? WindowManager.LayoutParams
            if (p != null) {
                p.width = WindowManager.LayoutParams.WRAP_CONTENT
                p.height = WindowManager.LayoutParams.WRAP_CONTENT
                safeUpdateViewLayout(view, p)
            }
        }

        btnToggleMenu?.setOnClickListener { vibrateFeedback(20L); updatePanelState(panelState + 1) }
        btnSingleBubble?.setOnClickListener { vibrateFeedback(20L); updatePanelState(0) }

        btnPlay?.setOnClickListener {
            vibrateFeedback(30L)
            if (isPlaying) {
                btnPlay.setImageResource(R.drawable.ic_play)
                stopExecutionLoop()
            } else {
                btnPlay.setImageResource(R.drawable.ic_pause)
                startScript("default")
            }
        }

        btnAdd?.setOnClickListener { vibrateFeedback(20L); showAddActionMenu() }
        btnCapturePool?.setOnClickListener { vibrateFeedback(20L); showCaptureFrame() }
        btnHelpTutorial?.setOnClickListener { vibrateFeedback(20L); showTutorialCard() }
        btnClearAll?.setOnClickListener { vibrateFeedback(30L); clearAllActions() }
        btnRecord?.setOnClickListener { vibrateFeedback(20L); if (isRecording) stopOverlayRecording() else startOverlayRecording() }
        btnToggleJoystick?.setOnClickListener { vibrateFeedback(20L); showJoystickManipulator() }
        btnLoadScript?.setOnClickListener { vibrateFeedback(20L); showScriptsDialog() }
        btnHideNumbers?.setOnClickListener { vibrateFeedback(20L); toggleNumbersVisibility() }
        btnClose?.setOnClickListener { vibrateFeedback(20L); hideControlPanel(openMainApp = true) }

        safeAddView(view, params)
    }

    fun hideControlPanel(openMainApp: Boolean = false) {
        controlPanelView?.let { safeRemoveView(it); controlPanelView = null }
        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) { logError(this, e) }
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return
        val view = LayoutInflater.from(this).inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = createOverlayParams().apply { gravity = Gravity.CENTER }
        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            vibrateFeedback(20L)
            stopExecutionLoop()
        }
        safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let { safeRemoveView(it); stopButtonView = null }
    }

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(loadScriptByName(name))
        if (actionsList.isEmpty()) {
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        isPlaying = true
        startExecutionLoop()
    }

    fun startExecutionLoop() {
        if (executionThread != null) return
        executionThread = Thread {
            var index = 0
            uiHandler.post { hideControlPanel(); showFloatingStopButton() }

            while (isPlaying && actionsList.isNotEmpty()) {
                val cfg = actionsList[index]
                try { Thread.sleep(cfg.delay) } catch (_: InterruptedException) { break }
                if (!isPlaying) break

                when (cfg.type) {
                    ActionType.CLICK -> {
                        val (x, y) = resolveNormalizedPoint(cfg.xNorm, cfg.yNorm)
                        val jitter = randomOffset(cfg.randomRadius)
                        val fx = x + jitter.x
                        val fy = y + jitter.y
                        uiHandler.post { showClickVisualizer(fx, fy) }
                        performClickWithCallback(fx, fy, globalClickDurationMs)
                    }
                    ActionType.LONG_PRESS -> {
                        val (x, y) = resolveNormalizedPoint(cfg.xNorm, cfg.yNorm)
                        uiHandler.post { showClickVisualizer(x, y) }
                        performClickWithCallback(x, y, cfg.holdDuration)
                    }
                    ActionType.SWIPE -> {
                        val (sx, sy) = resolveNormalizedPoint(cfg.xNorm, cfg.yNorm)
                        val (ex, ey) = resolveNormalizedPoint(cfg.endXNorm, cfg.endYNorm)
                        if (cfg.joystickPath.isNotEmpty()) {
                            val path = cfg.joystickPath.map { p ->
                                val normP = resolveNormalizedPoint(p.x, p.y)
                                PointF(normP.first, normP.second)
                            }
                            performPathSwipeWithCallback(path, sx, sy, ex, ey, cfg.holdDuration)
                        } else {
                            performSwipeWithCallback(sx, sy, ex, ey, cfg.holdDuration)
                        }
                    }
                    ActionType.TRIGGER -> {
                        val jump = executeAiTriggerSequence(cfg)
                        if (jump == -999) { index = 0; continue }
                        else if (jump > 0) {
                            val targetIdx = actionsList.indexOfFirst { it.id == jump }
                            if (targetIdx != -1) { index = targetIdx; continue }
                        }
                    }
                }
                index = (index + 1) % actionsList.size
            }
            isPlaying = false
            uiHandler.post { stopExecutionLoop() }
        }
        executionThread?.start()
    }

    fun stopExecutionLoop() {
        isPlaying = false
        executionThread?.interrupt()
        executionThread = null
        uiHandler.post { hideFloatingStopButton(); showControlPanel() }
    }

    fun startOverlayRecording() {
        isRecording = true
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        hideControlPanel()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        showControlPanel()
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
            act.startView?.let { safeRemoveView(it) }
            act.endView?.let { safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(posX: Float, posY: Float, delay: Long, type: ActionType, id: Int) {
        val actionId = if (id == -1) (actionsList.size + 1) else id
        val startView = LayoutInflater.from(this).inflate(R.layout.floating_target, null)
        val tvNum = startView.findViewById<TextView>(R.id.tvTargetNumber)
        tvNum?.text = actionId.toString()

        val sizePx = dpToPx(if (type == ActionType.TRIGGER) 50 else 36)
        val params = createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        val config = ActionConfig(
            id = actionId,
            startView = startView,
            type = type,
            delay = delay,
            xNorm = normalizeX(posX),
            yNorm = normalizeY(posY)
        )

        startView.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0; private var initY = 0
            private var touchX = 0f; private var touchY = 0f
            private var isMoving = false

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        isMoving = false
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = abs(event.rawX - touchX)
                        val dy = abs(event.rawY - touchY)
                        if (dx > 8 || dy > 8) {
                            isMoving = true
                            val (sw, sh) = getRealScreenSize()
                            val sz = if (startView.width > 0) startView.width else dpToPx(36)
                            params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - sz).coerceAtLeast(0))
                            params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - sz).coerceAtLeast(0))
                            config.xNorm = normalizeX(params.x + sz / 2f)
                            config.yNorm = normalizeY(params.y + sz / 2f)
                            safeUpdateViewLayout(startView, params)
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

        if (isRecording || isNumbersHidden) startView.visibility = View.INVISIBLE
        actionsList.add(config)
        safeAddView(startView, params)
    }

    fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = dpToPx(36)
        val params = createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        endView.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0; private var initY = 0
            private var touchX = 0f; private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val (sw, sh) = getRealScreenSize()
                        val sz = if (endView.width > 0) endView.width else dpToPx(36)
                        params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - sz).coerceAtLeast(0))
                        params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - sz).coerceAtLeast(0))
                        config.endXNorm = normalizeX(params.x + sz / 2f)
                        config.endYNorm = normalizeY(params.y + sz / 2f)
                        safeUpdateViewLayout(endView, params)
                        return true
                    }
                    MotionEvent.ACTION_UP -> { v.performClick(); return true }
                }
                return false
            }
        })

        if (isRecording || isNumbersHidden) endView.visibility = View.INVISIBLE
        config.endView = endView
        safeAddView(endView, params)
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_beacon_ring, null)
        val params = createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }
        safeAddView(view, params)
        view.animate().alpha(0f).setDuration(300).withEndAction { safeRemoveView(view) }.start()
    }

    fun showCaptureFrame() {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_capture_frame, null)
        captureFrameView = view
        val params = createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
        }

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        btnDoCapture?.setOnClickListener {
            vibrateFeedback(40L)
            safeRemoveView(view)
            val (sw, sh) = getRealScreenSize()
            addNewActionAtPosition(sw / 2f, sh / 2f, 1000L, ActionType.TRIGGER, -1)
            Toast.makeText(this, "🎉 ИИ-Шаблон добавлен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun showJoystickManipulator() {
        if (joystickOverlayView != null) return
        val view = LayoutInflater.from(this).inflate(R.layout.floating_joystick_control, null)
        joystickOverlayView = view

        val sizePx = dpToPx(160)
        val params = createOverlayParams().apply {
            width = sizePx
            height = sizePx + dpToPx(40)
            gravity = Gravity.TOP or Gravity.START
            x = dpToPx(30)
            y = dpToPx(200)
        }

        val handleMove = view.findViewById<View>(R.id.handleMoveJoystick)
        val btnClose = view.findViewById<View>(R.id.btnCloseJoystick)
        val btnRecordJoystick = view.findViewById<Button>(R.id.btnRecordJoystick)
        val viewKnob = view.findViewById<View>(R.id.viewJoystickKnob)

        var isJoystickRecording = false
        var joystickStartTime = 0L
        var startX = 0f
        var startY = 0f
        val recordedPathPoints = ArrayList<PointF>()

        handleMove?.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0; private var initY = 0
            private var touchX = 0f; private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val (sw, sh) = getRealScreenSize()
                        params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - sizePx).coerceAtLeast(0))
                        params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - sizePx).coerceAtLeast(0))
                        safeUpdateViewLayout(view, params)
                        return true
                    }
                }
                return false
            }
        })

        viewKnob?.setOnTouchListener(object : View.OnTouchListener {
            private var maxRadiusPx = dpToPx(50).toFloat()

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        startX = event.rawX
                        startY = event.rawY
                        joystickStartTime = System.currentTimeMillis()
                        recordedPathPoints.clear()
                        recordedPathPoints.add(PointF(startX, startY))
                        vibrateFeedback(20L)
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = event.rawX - startX
                        val dy = event.rawY - startY
                        val dist = hypot(dx.toDouble(), dy.toDouble()).toFloat()
                        val angle = Math.atan2(dy.toDouble(), dx.toDouble())
                        val clampedDist = min(dist, maxRadiusPx)

                        val knobX = (clampedDist * Math.cos(angle)).toFloat()
                        val knobY = (clampedDist * Math.sin(angle)).toFloat()

                        viewKnob.translationX = knobX
                        viewKnob.translationY = knobY

                        if (isJoystickRecording) {
                            recordedPathPoints.add(PointF(startX + knobX, startY + knobY))
                        }
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        val duration = (System.currentTimeMillis() - joystickStartTime).coerceIn(100L, 5000L)
                        val finalDx = viewKnob.translationX
                        val finalDy = viewKnob.translationY
                        val finalDist = hypot(finalDx.toDouble(), finalDy.toDouble()).toFloat()

                        viewKnob.animate().translationX(0f).translationY(0f).setDuration(180).start()

                        if (finalDist > 15) {
                            val centerX = params.x + sizePx / 2f
                            val centerY = params.y + dpToPx(30) + sizePx / 2f
                            val targetX = centerX + finalDx
                            val targetY = centerY + finalDy

                            performSwipeWithCallback(centerX, centerY, targetX, targetY, duration)

                            if (isJoystickRecording) {
                                val normPath = ArrayList<PointF>().apply {
                                    recordedPathPoints.forEach { p ->
                                        add(PointF(normalizeX(p.x), normalizeY(p.y)))
                                    }
                                }
                                val first = normPath.firstOrNull() ?: PointF(normalizeX(centerX), normalizeY(centerY))
                                val last = normPath.lastOrNull() ?: PointF(normalizeX(targetX), normalizeY(targetY))

                                val cfg = ActionConfig(
                                    id = actionsList.size + 1,
                                    type = ActionType.SWIPE,
                                    xNorm = first.x,
                                    yNorm = first.y,
                                    endXNorm = last.x,
                                    endYNorm = last.y,
                                    holdDuration = duration,
                                    joystickPath = normPath
                                )

                                actionsList.add(cfg)
                                spawnEndTargetAtPosition(cfg, targetX, targetY)
                                Toast.makeText(
                                    this@MyAutoClickService,
                                    "🕹 Записано движение джойстика (${duration}мс)!",
                                    Toast.LENGTH_SHORT
                                ).show()
                            }
                        }
                        return true
                    }
                }
                return false
            }
        })

        btnRecordJoystick?.setOnClickListener {
            vibrateFeedback(25L)
            isJoystickRecording = !isJoystickRecording
            btnRecordJoystick.text = if (isJoystickRecording) "🔴 Запись..." else "⏺ ЗАПИСАТЬ"
            btnRecordJoystick.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isJoystickRecording) R.color.red_close else R.color.accent_blue))
        }

        btnClose?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view); joystickOverlayView = null }
        safeAddView(view, params)
    }

    fun showEditDialog(config: ActionConfig) {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_edit_dialog, null)
        val params = createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            flags = WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
        }

        val tvTitle = view.findViewById<TextView>(R.id.tvDialogTitle)
        val etDelay = view.findViewById<EditText>(R.id.etDelay)
        val etRepeat = view.findViewById<EditText>(R.id.etRepeatCount)
        val etRadius = view.findViewById<EditText>(R.id.etRandomRadius)
        val etHold = view.findViewById<EditText>(R.id.etHoldDuration)
        val btnSave = view.findViewById<Button>(R.id.btnSave)
        val btnCancel = view.findViewById<Button>(R.id.btnCancel)

        tvTitle?.text = "Шаг #${config.id}"
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeat?.setText(config.repeatCount.toString())
        etRadius?.setText(config.randomRadius.toString())
        etHold?.setText(config.holdDuration.toString())

        btnSave?.setOnClickListener {
            vibrateFeedback(30L)
            config.delay = ((etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0) * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHold?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L
            safeRemoveView(view)
            Toast.makeText(this, "Шаг #${config.id} сохранен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun showScriptsDialog() {
        val view = LayoutInflater.from(this).inflate(R.layout.dialog_scripts, null)
        val params = createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val etName = view.findViewById<EditText>(R.id.etScriptName)
        val btnSave = view.findViewById<Button>(R.id.btnSaveScriptAction)
        val btnClose = view.findViewById<Button>(R.id.btnCloseScripts)

        btnSave?.setOnClickListener {
            val name = etName?.text?.toString()?.trim() ?: ""
            if (name.isNotEmpty()) {
                saveScriptByName(name, actionsList)
                etName?.setText("")
            }
        }

        btnClose?.setOnClickListener { safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun showAddActionMenu() {
        val view = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val btnClick = view.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = view.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = view.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = view.findViewById<Button>(R.id.btnCancelAdd)

        val (sw, sh) = getRealScreenSize()
        val spawnX = sw / 2f
        val spawnY = sh / 2f

        btnClick?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1); safeRemoveView(view) }
        btnSwipe?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1); spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f); safeRemoveView(view) }
        btnAi?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0); safeRemoveView(view) }
        btnCancel?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }

        safeAddView(view, params)
    }

    fun showTutorialCard() {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        val params = createOverlayParams().apply { gravity = Gravity.CENTER }
        val btnSkip = view.findViewById<Button>(R.id.btnTutSkip)
        btnSkip?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun executeAiTriggerSequence(config: ActionConfig): Int {
        val screen = captureScreenBitmap() ?: return -1
        val match = TemplateMatcher.findCandidatesForCreation(screen, screen).firstOrNull()
        if (match != null) {
            if (config.clickAiTarget) {
                performClickWithCallback(match.rect.centerX().toFloat(), match.rect.centerY().toFloat(), globalClickDurationMs)
            }
            if (config.jumpToStepOnMatch > 0) return config.jumpToStepOnMatch
            if (config.targetScriptToLoad.isNotEmpty()) {
                loadScriptByName(config.targetScriptToLoad)
                return -999
            }
        }
        return -1
    }

    private fun getScriptsDir(): File {
        val dir = File(filesDir, "scripts")
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun loadScriptByName(name: String): List<ActionConfig> {
        val list = ArrayList<ActionConfig>()
        try {
            val file = File(getScriptsDir(), "$name.json")
            if (file.exists()) {
                val jsonArray = JSONArray(file.readText())
                for (i in 0 until jsonArray.length()) {
                    list.add(ActionConfig.fromJson(jsonArray.getJSONObject(i)))
                }
            }
        } catch (e: Exception) { logError(this, e) }
        return list
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        try {
            val file = File(getScriptsDir(), "$name.json")
            val bakFile = File(getScriptsDir(), "$name.json.bak")
            if (file.exists()) file.copyTo(bakFile, overwrite = true)

            val jsonArray = JSONArray()
            actions.forEach { jsonArray.put(it.toJson()) }
            file.writeText(jsonArray.toString(2))
            Toast.makeText(this, "Сценарий '$name' сохранен!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) { logError(this, e) }
    }

    fun loadAllTemplatesFromDisk() {
        try {
            globalTemplates.forEach { try { it.recycle() } catch (_: Exception) {} }
            globalTemplates.clear()
            globalTemplatesNames.clear()

            val baseDir = File(filesDir, "templates")
            if (baseDir.exists()) {
                baseDir.walkTopDown().filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }.forEach { file ->
                    BitmapFactory.decodeFile(file.absolutePath)?.let { bmp ->
                        globalTemplates.add(bmp)
                        globalTemplatesNames.add(file.absolutePath)
                    }
                }
            }
        } catch (e: Exception) { logError(this, e) }
    }

    fun moveTemplateToTrash(index: Int) {
        if (index !in globalTemplatesNames.indices) return
        try {
            val maskPath = globalTemplatesNames[index]
            val maskFile = File(maskPath)
            if (maskFile.exists()) maskFile.delete()
            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)
            Toast.makeText(this, "🗑 Шаблон удален", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) { logError(this, e) }
    }

    fun exportScriptWithTemplates(context: Context, scriptName: String) {
        try {
            val scriptFile = File(getScriptsDir(), "$scriptName.json")
            if (!scriptFile.exists()) return
            val zipFile = File(context.externalCacheDir ?: context.cacheDir, "$scriptName.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))
            zos.putNextEntry(ZipEntry("scripts/$scriptName.json"))
            zos.write(scriptFile.readBytes())
            zos.closeEntry()
            zos.close()

            val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", zipFile)
            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(Intent.createChooser(shareIntent, "Экспорт сценария"))
        } catch (e: Exception) { logError(context, e) }
    }

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        bgScannerExecutor.shutdown()
        super.onDestroy()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    print("✨ Функция записи джойстика и отправка траекторий жестов успешно восстановлены!")

if __name__ == "__main__":
    fix_joystick_recording()