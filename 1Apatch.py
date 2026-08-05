import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Исправлен и обновлен модуль: {rel_path}")

def fix_all_reported_issues_v37_5():
    print("🚀 Исправление создания шагов, калибровки ИИ, положения меню, подсказок и джойстика v37.5.0-PRO...")

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
        versionCode = 2570
        versionName = "37.5.0-PRO"

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

    # 2. ControlPanelOverlay.kt (Смещение начальной позиции меню вниз до Y = 240dp)
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
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_control_panel, OverlayLayer.PANEL, OverlayPriority.MEDIUM) {

    private var stopButtonView: View? = null
    private var panelState = 0

    private var btnPlay: ImageButton? = null
    private var btnAdd: ImageButton? = null
    private var btnCapturePool: ImageButton? = null
    private var btnHelpTutorial: ImageButton? = null
    private var btnToggleMenu: ImageButton? = null

    private var btnClearAll: ImageButton? = null
    private var btnRecord: ImageButton? = null
    private var btnToggleJoystick: ImageButton? = null
    private var btnLoadScript: ImageButton? = null
    private var btnHideNumbers: ImageButton? = null
    private var btnClose: ImageButton? = null
    private var btnSingleBubble: ImageButton? = null

    private var layoutMainRow: View? = null
    private var layoutSubMenu: View? = null

    override fun onViewInflated(view: View) {
        val handleDrag = view.findViewById<TextView>(R.id.handleDrag)
        layoutMainRow = view.findViewById(R.id.layoutMainRow)
        layoutSubMenu = view.findViewById(R.id.layoutSubMenu)
        btnSingleBubble = view.findViewById(R.id.btnSingleBubble)

        btnPlay = view.findViewById(R.id.btnPlay)
        btnAdd = view.findViewById(R.id.btnAdd)
        btnCapturePool = view.findViewById(R.id.btnCapturePool)
        btnHelpTutorial = view.findViewById(R.id.btnHelpTutorial)
        btnToggleMenu = view.findViewById(R.id.btnToggleMenu)

        btnClearAll = view.findViewById(R.id.btnClearAll)
        btnRecord = view.findViewById(R.id.btnRecord)
        btnToggleJoystick = view.findViewById(R.id.btnToggleJoystick)
        btnLoadScript = view.findViewById(R.id.btnLoadScript)
        btnHideNumbers = view.findViewById(R.id.btnHideNumbers)
        btnClose = view.findViewById(R.id.btnClose)

        var initX = 0; var initY = 0; var touchX = 0f; var touchY = 0f

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
                    val (screenW, screenH) = service.overlayManager.getRealScreenSize()
                    val w = if (view.width > 0) view.width else service.dpToPx(180)
                    val h = if (view.height > 0) view.height else service.dpToPx(50)
                    val maxX = (screenW - w).coerceAtLeast(0)
                    val maxY = (screenH - h).coerceAtLeast(0)

                    p.gravity = Gravity.TOP or Gravity.START
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    // Ограничиваем сверху 60dp, чтобы не цеплять шторку
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(service.dpToPx(60), maxY)
                    service.overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        btnToggleMenu?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(panelState + 1) }
        btnSingleBubble?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(0) }

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (service.isPlaying) {
                btnPlay?.setImageResource(R.drawable.ic_play)
                service.stopExecutionLoop()
            } else {
                btnPlay?.setImageResource(R.drawable.ic_pause)
                service.startScript("default")
            }
        }

        btnAdd?.setOnClickListener { service.vibrateFeedback(20L); service.showAddActionMenu() }
        btnCapturePool?.setOnClickListener { service.vibrateFeedback(20L); service.captureFrameOverlay.show() }
        btnHelpTutorial?.setOnClickListener { service.vibrateFeedback(20L); service.showTutorialCard() }
        btnClearAll?.setOnClickListener { service.vibrateFeedback(30L); service.clearAllActions() }
        btnRecord?.setOnClickListener { service.vibrateFeedback(20L); if (service.isRecording) service.stopOverlayRecording() else service.startOverlayRecording() }
        btnToggleJoystick?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.joystickOverlay.rootView != null) service.joystickOverlay.hide() else service.joystickOverlay.show()
        }
        btnLoadScript?.setOnClickListener { service.vibrateFeedback(20L); service.showScriptsDialog() }
        btnHideNumbers?.setOnClickListener { service.vibrateFeedback(20L); service.toggleNumbersVisibility() }
        btnClose?.setOnClickListener { service.vibrateFeedback(20L); service.hideControlPanel(openMainApp = true) }
    }

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = service.dpToPx(20)
            y = service.dpToPx(240) // Смещено ниже от шторки Android
        }
    }

    fun ensureSubMenuVisible() {
        if (panelState != 1) {
            updatePanelState(1)
        }
    }

    fun getButtonForStep(step: Int): View? {
        return when (step) {
            0 -> btnPlay
            1 -> btnAdd
            2 -> btnCapturePool
            3 -> btnHelpTutorial
            4 -> btnToggleMenu
            5 -> btnClearAll
            6 -> btnRecord
            7 -> btnToggleJoystick
            8 -> btnLoadScript
            9 -> btnHideNumbers
            10 -> btnClose
            else -> null
        }
    }

    fun resetAllButtonScales() {
        val buttons = listOf(
            btnPlay, btnAdd, btnCapturePool, btnHelpTutorial, btnToggleMenu,
            btnClearAll, btnRecord, btnToggleJoystick, btnLoadScript, btnHideNumbers, btnClose
        )
        buttons.forEach { btn ->
            btn?.scaleX = 1.0f
            btn?.scaleY = 1.0f
        }
    }

    fun updatePanelState(state: Int) {
        panelState = state % 3
        when (panelState) {
            0 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.GONE }
            1 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.VISIBLE; btnSingleBubble?.visibility = View.GONE }
            2 -> { layoutMainRow?.visibility = View.GONE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.VISIBLE }
        }
        rootView?.requestLayout()
        val p = rootView?.layoutParams as? WindowManager.LayoutParams
        if (p != null && rootView != null) {
            val (screenW, screenH) = service.overlayManager.getRealScreenSize()
            p.width = WindowManager.LayoutParams.WRAP_CONTENT
            p.height = WindowManager.LayoutParams.WRAP_CONTENT
            p.gravity = Gravity.TOP or Gravity.START

            rootView?.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED)
            val h = if (rootView?.measuredHeight ?: 0 > 0) rootView!!.measuredHeight else service.dpToPx(105)
            val w = if (rootView?.measuredWidth ?: 0 > 0) rootView!!.measuredWidth else service.dpToPx(200)

            p.x = p.x.coerceIn(0, (screenW - w).coerceAtLeast(0))
            p.y = p.y.coerceIn(service.dpToPx(60), (screenH - h).coerceAtLeast(service.dpToPx(60)))

            service.overlayManager.safeUpdateViewLayout(rootView, p)
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return
        val view = LayoutInflater.from(service).inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val (screenW, _) = service.overlayManager.getRealScreenSize()
        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = (screenW - service.dpToPx(80)) / 2
            y = service.dpToPx(80)
        }

        val handleDrag = view.findViewById<TextView>(R.id.handleDragStop)
        var initX = 0; var initY = 0
        var touchX = 0f; var touchY = 0f

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
                    val (sw, sh) = service.overlayManager.getRealScreenSize()
                    val w = if (view.width > 0) view.width else service.dpToPx(80)
                    val h = if (view.height > 0) view.height else service.dpToPx(40)
                    p.gravity = Gravity.TOP or Gravity.START
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - w).coerceAtLeast(0))
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(service.dpToPx(50), (sh - h).coerceAtLeast(service.dpToPx(50)))
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
        stopButtonView?.let { service.overlayManager.safeRemoveView(it) }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_beacon_ring, null)
        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }
        service.overlayManager.safeAddView(view, params)
        view.animate().alpha(0f).setDuration(300).withEndAction { service.overlayManager.safeRemoveView(view) }.start()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt", control_panel_code)

    # 3. JoystickOverlay.kt (Исправление перемещения джойстика)
    joystick_code = r"""package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.PointF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import kotlin.math.hypot
import kotlin.math.min

class JoystickOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_joystick_control, OverlayLayer.JOYSTICK, OverlayPriority.HIGH) {

    private var handleMove: View? = null
    private var btnRecord: Button? = null
    private var btnClose: ImageButton? = null
    private var touchArea: View? = null
    private var viewKnob: View? = null

    private val rawPoints = ArrayList<PointF>()
    private val smoothedPoints = ArrayList<PointF>()
    private var isRecordingPath = false
    private var joystickStartTime = 0L

    override fun onViewInflated(view: View) {
        handleMove = view.findViewById(R.id.handleMoveJoystick)
        btnRecord = view.findViewById(R.id.btnRecordJoystick)
        btnClose = view.findViewById(R.id.btnCloseJoystick)
        touchArea = view.findViewById(R.id.viewJoystickBase)
        viewKnob = view.findViewById(R.id.viewJoystickKnob)

        bindInteractions()
    }

    override fun createParams(): WindowManager.LayoutParams {
        val sizePx = service.dpToPx(160)
        return service.overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx + service.dpToPx(40)
            gravity = Gravity.TOP or Gravity.START
            x = service.dpToPx(30)
            y = service.dpToPx(240)
        }
    }

    private fun bindInteractions() {
        var initX = 0; var initY = 0
        var touchX = 0f; var touchY = 0f

        handleMove?.setOnTouchListener { _, event ->
            val p = rootView?.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x; initY = p.y
                    touchX = event.rawX; touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (screenW, screenH) = service.overlayManager.getRealScreenSize()
                    val sizePx = service.dpToPx(160)
                    p.gravity = Gravity.TOP or Gravity.START
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (screenW - sizePx).coerceAtLeast(0))
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(service.dpToPx(60), (screenH - sizePx).coerceAtLeast(service.dpToPx(60)))
                    service.overlayManager.safeUpdateViewLayout(rootView, p)
                    true
                }
                else -> false
            }
        }

        var startX = 0f; var startY = 0f
        val maxRadiusPx = service.dpToPx(50).toFloat()

        viewKnob?.setOnTouchListener(object : View.OnTouchListener {
            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        startX = event.rawX; startY = event.rawY
                        joystickStartTime = System.currentTimeMillis()
                        rawPoints.clear()
                        rawPoints.add(PointF(startX, startY))
                        service.vibrateFeedback(20L)
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

                        viewKnob?.translationX = knobX
                        viewKnob?.translationY = knobY

                        if (isRecordingPath) {
                            val pt = PointF(startX + knobX, startY + knobY)
                            val last = rawPoints.lastOrNull()
                            if (last == null || hypot((pt.x - last.x).toDouble(), (pt.y - last.y).toDouble()) > 3.0) {
                                rawPoints.add(pt)
                            }
                        }
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        val duration = (System.currentTimeMillis() - joystickStartTime).coerceIn(100L, 5000L)
                        val finalDx = viewKnob?.translationX ?: 0f
                        val finalDy = viewKnob?.translationY ?: 0f
                        val finalDist = hypot(finalDx.toDouble(), finalDy.toDouble()).toFloat()

                        viewKnob?.animate()?.translationX(0f)?.translationY(0f)?.setDuration(180)?.start()

                        if (finalDist > 15) {
                            val params = rootView?.layoutParams as? WindowManager.LayoutParams
                            val sizePx = service.dpToPx(160)
                            val centerX = (params?.x ?: 0) + sizePx / 2f
                            val centerY = (params?.y ?: 0) + service.dpToPx(30) + sizePx / 2f
                            val targetX = centerX + finalDx
                            val targetY = centerY + finalDy

                            smoothPathTrajectory()
                            service.performSwipeWithCallback(centerX, centerY, targetX, targetY, duration)

                            if (isRecordingPath) {
                                val normPath = ArrayList<PointF>().apply {
                                    smoothedPoints.forEach { p ->
                                        add(PointF(service.normalizeX(p.x), service.normalizeY(p.y)))
                                    }
                                }
                                val first = normPath.firstOrNull() ?: PointF(service.normalizeX(centerX), service.normalizeY(centerY))
                                val last = normPath.lastOrNull() ?: PointF(service.normalizeX(targetX), service.normalizeY(targetY))

                                val cfg = ActionConfig(
                                    id = service.actionsList.size + 1,
                                    type = ActionType.SWIPE_PATH,
                                    xNorm = first.x,
                                    yNorm = first.y,
                                    endXNorm = last.x,
                                    endYNorm = last.y,
                                    holdDuration = duration,
                                    joystickPath = normPath
                                )

                                service.actionsList.add(cfg)
                                service.spawnEndTargetAtPosition(cfg, targetX, targetY)
                                Toast.makeText(service, "🕹 Записано движение джойстика (${duration}мс)!", Toast.LENGTH_SHORT).show()
                            }
                        }
                        return true
                    }
                }
                return false
            }
        })

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(25L)
            isRecordingPath = !isRecordingPath
            btnRecord?.text = if (isRecordingPath) "🔴 Запись..." else "⏺ ЗАПИСАТЬ"
            btnRecord?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isRecordingPath) R.color.red_close else R.color.accent_blue))
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }
    }

    private fun smoothPathTrajectory() {
        smoothedPoints.clear()
        if (rawPoints.size < 3) {
            smoothedPoints.addAll(rawPoints)
            return
        }

        smoothedPoints.add(rawPoints.first())
        for (i in 1 until rawPoints.size - 1) {
            val prev = rawPoints[i - 1]
            val curr = rawPoints[i]
            val next = rawPoints[i + 1]

            val smX = (prev.x + curr.x + next.x) / 3f
            val smY = (prev.y + curr.y + next.y) / 3f
            smoothedPoints.add(PointF(smX, smY))
        }
        smoothedPoints.add(rawPoints.last())
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/JoystickOverlay.kt", joystick_code)

    # 4. MyAutoClickService.kt (Настоящий захват снимка экрана + Защита от прыжков подсказок)
    service_code = r"""package com.example.autotap

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

        logAppEvent(this, "SERVICE", "🚀 Служба AutoTap v37.5.0-PRO успешно подключена к системе")
        Toast.makeText(this, "AutoTap v37.5.0-PRO запущен", Toast.LENGTH_SHORT).show()
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
        val startView = LayoutInflater.from(this).inflate(R.layout.floating_target, null)
        val tvNum = startView.findViewById<TextView>(R.id.tvTargetNumber)
        tvNum?.text = actionId.toString()

        val sizePx = overlayManager.dpToPx(if (type == ActionType.TRIGGER) 50 else 36)
        val params = overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            this.x = (x - sizePx / 2f).toInt()
            this.y = (y - sizePx / 2f).toInt()
        }

        val config = ActionConfig(
            id = actionId,
            startView = startView,
            type = type,
            delay = delay,
            xNorm = normalizeX(x),
            yNorm = normalizeY(y)
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
                            val (sw, sh) = overlayManager.getRealScreenSize()
                            val sz = if (startView.width > 0) startView.width else overlayManager.dpToPx(36)
                            params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - sz).coerceAtLeast(0))
                            params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - sz).coerceAtLeast(0))
                            config.xNorm = normalizeX(params.x + sz / 2f)
                            config.yNorm = normalizeY(params.y + sz / 2f)
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

        if (isRecording || isNumbersHidden) startView.visibility = View.INVISIBLE
        actionsList.add(config)
        overlayManager.safeAddView(startView, params)
        logAppEvent(this, "STEP_ADD", "✅ Мишень шага #$actionId успешно создана и добавлена на экран")
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

    // Настоящий захват снимка экрана через Accessibility API
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

    // --- ANCHOR TUTORIAL & HIGHLIGHTING ---

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

    fun hideTutorial() {
        clearButtonHighlights()
        isTutorialActive = false
        tutorialCardView?.let {
            overlayManager.safeRemoveView(it)
            tutorialCardView = null
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

        val screenSize = overlayManager.getRealScreenSize()
        val spawnX = screenSize.first / 2f
        val spawnY = screenSize.second / 2f

        btnClick?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1); overlayManager.safeRemoveView(dialogView) }
        btnSwipe?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1); spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f); overlayManager.safeRemoveView(dialogView) }
        btnAi?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0); overlayManager.safeRemoveView(dialogView) }
        btnCancel?.setOnClickListener { vibrateFeedback(20L); overlayManager.safeRemoveView(dialogView) }

        overlayManager.safeAddView(dialogView, params)
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
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    print("✨ Исправление захвата экрана, создания шагов и подсказок v37.5.0-PRO завершено!")

if __name__ == "__main__":
    fix_all_reported_issues_v37_5()