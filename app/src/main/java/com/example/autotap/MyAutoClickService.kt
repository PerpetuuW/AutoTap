package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.Point
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import androidx.annotation.RequiresApi
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

class MyAutoClickService : AccessibilityService() {

    companion object {
        @Volatile
        var instance: MyAutoClickService? = null
            private set
    }

    internal val actionsList = CopyOnWriteArrayList<AutoTapAction>()
    internal lateinit var overlayManager: OverlayManager

    // Публичные объекты оверлеев и движков для взаимодействия с MainActivity и скриптами
    var debuggerOverlay: Any? = null
    var captureFrameOverlay: Any? = null
    var joystickOverlay: Any? = null
    var scriptExecutor: Any? = null
    var gestureExecutor: Any? = null
    var aiScannerEngine: Any? = null
    var templateRepository: Any? = null

    private lateinit var windowManager: WindowManager
    private var overlayView: View? = null
    private var statusTextView: TextView? = null

    private val isRunningState = AtomicBoolean(false)
    private lateinit var scriptManager: AtomicScriptManager
    private lateinit var executorThread: HandlerThread
    private lateinit var executorHandler: Handler
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        instance = this
        scriptManager = AtomicScriptManager(this)
        overlayManager = OverlayManager(this)
        executorThread = HandlerThread("AutoTapExecutorThread").apply { start() }
        executorHandler = Handler(executorThread.looper)
        DiagnosticLogger.log("MyAutoClickService", "Service onCreate executed")
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        DiagnosticLogger.log("MyAutoClickService", "Accessibility Service Connected")
        checkBatteryOptimizations()
        setupOverlayUI()
    }

    private fun checkBatteryOptimizations() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(PowerManager::class.java)
            if (pm != null && !pm.isIgnoringBatteryOptimizations(packageName)) {
                val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                    data = Uri.parse("package:$packageName")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
            }
        }
    }

    fun getRealScreenSize(): Point {
        val wm = getSystemService(WindowManager::class.java)
        val display = wm.defaultDisplay
        val size = Point()
        display.getRealSize(size)
        return size
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupOverlayUI() {
        if (!Settings.canDrawOverlays(this)) return

        windowManager = getSystemService(WindowManager::class.java)
        val (screenWidth, screenHeight) = getRealScreenSize()

        val layoutParams = WindowManager.LayoutParams().apply {
            type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }

            this.gravity = Gravity.TOP or Gravity.START
            this.x = normalizeX(10.dpToPx(this@MyAutoClickService), screenWidth)
            this.y = normalizeY(100.dpToPx(this@MyAutoClickService), screenHeight)
            this.width = WindowManager.LayoutParams.WRAP_CONTENT
            this.height = WindowManager.LayoutParams.WRAP_CONTENT
        }

        val container = FrameLayout(this).apply {
            setBackgroundColor(Color.argb(220, 20, 20, 20))
            setPadding(12.dpToPx(context), 12.dpToPx(context), 12.dpToPx(context), 12.dpToPx(context))
        }

        val statusTv = TextView(this).apply {
            text = "Status: READY"
            setTextColor(Color.WHITE)
            textSize = 12f
        }
        statusTextView = statusTv

        val toggleBtn = Button(this).apply {
            text = "START / STOP"
            setOnClickListener {
                vibrateFeedback(40L)
                if (isRunningState.get()) {
                    stopExecution()
                } else {
                    startExecution()
                }
            }
        }

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(statusTv)
            addView(toggleBtn)
        }
        container.addView(layout)

        container.setOnTouchListener(object : View.OnTouchListener {
            private var initialX = 0
            private var initialY = 0
            private var touchX = 0f
            private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = layoutParams.x
                        initialY = layoutParams.y
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val newX = initialX + (event.rawX - touchX).toInt()
                        val newY = initialY + (event.rawY - touchY).toInt()
                        layoutParams.x = normalizeX(newX, screenWidth)
                        layoutParams.y = normalizeY(newY, screenHeight)
                        windowManager.updateViewLayout(container, layoutParams)
                        return true
                    }
                }
                return false
            }
        })

        overlayView = container
        windowManager.addView(overlayView, layoutParams)
    }

    // Методы управления панелями и режимами
    fun showControlPanel() { setupOverlayUI() }
    fun hideControlPanel() { stopExecution() }
    fun showFloatingStopButton() {}
    fun hideFloatingStopButton() {}
    fun stopExecutionLoop() { stopExecution() }
    fun startScript(name: String) { startExecution() }
    fun saveScriptByName(name: String) { scriptManager.saveScript(name, actionsList) }
    fun loadScriptByName(name: String) {
        val loaded = scriptManager.loadScript(name)
        actionsList.clear()
        actionsList.addAll(loaded)
    }

    fun loadAllTemplatesFromDisk() {}
    fun exportScriptWithTemplates(name: String) {}
    fun moveTemplateToTrash(name: String) {}
    fun addNewActionAtPosition(x: Int, y: Int, type: ActionType = ActionType.CLICK) {
        actionsList.add(AutoTapAction(x = x, y = y, type = type))
    }
    fun clearAllActions() { actionsList.clear() }
    fun showAddActionMenu() {}
    fun showTutorialCard() {}
    fun showScriptsDialog() {}
    fun showScriptPickerDialog(callback: (String) -> Unit) {}
    fun toggleNumbersVisibility() {}
    fun startOverlayRecording() { isRecording = true }
    fun stopOverlayRecording() { isRecording = false }
    fun spawnEndTargetAtPosition(x: Int, y: Int, num: Int) = overlayManager.spawnEndTargetAtPosition(x, y, num)
    fun showClickVisualizer(x: Int, y: Int) {}

    fun captureScreenBitmap(callback: (Bitmap?) -> Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            takeScreenshot(
                android.view.Display.DEFAULT_DISPLAY,
                applicationContext.mainExecutor,
                object : TakeScreenshotCallback {
                    override fun onSuccess(screenshotResult: ScreenshotResult) {
                        try {
                            val hardwareBuffer = screenshotResult.hardwareBuffer
                            val bitmap = Bitmap.wrapHardwareBuffer(hardwareBuffer, screenshotResult.colorSpace)
                                ?.copy(Bitmap.Config.ARGB_8888, false)
                            hardwareBuffer.close()
                            callback(bitmap)
                        } catch (e: Exception) {
                            callback(null)
                        }
                    }
                    override fun onFailure(errorCode: Int) { callback(null) }
                }
            )
        } else {
            callback(null)
        }
    }

    fun performClickWithCallback(x: Int, y: Int, durationMs: Long, callback: (Boolean) -> Unit) {
        val success = performClickSync(x, y, durationMs)
        callback(success)
    }

    fun startExecution() {
        if (isRunningState.compareAndSet(false, true)) {
            isPlaying = true
            val loaded = scriptManager.loadScript("default_scenario")
            actionsList.clear()
            if (loaded.isNotEmpty()) {
                actionsList.addAll(loaded)
            } else {
                val (screenWidth, screenHeight) = getRealScreenSize()
                actionsList.add(AutoTapAction(x = screenWidth / 2, y = screenHeight / 2))
            }
            mainHandler.post { statusTextView?.text = "Status: RUNNING" }
            executorHandler.post { runExecutionLoop() }
        }
    }

    fun stopExecution() {
        if (isRunningState.compareAndSet(true, false)) {
            isPlaying = false
            mainHandler.post { statusTextView?.text = "Status: STOPPED" }
        }
    }

    private fun runExecutionLoop() {
        val (screenWidth, screenHeight) = getRealScreenSize()

        while (isRunningState.get()) {
            for (action in actionsList) {
                if (!isRunningState.get()) break
                val normX = normalizeX(action.x, screenWidth)
                val normY = normalizeY(action.y, screenHeight)

                when (action.type) {
                    ActionType.CLICK -> performClickSync(normX, normY, action.durationMs)
                    ActionType.SWIPE -> {
                        val normEndX = normalizeX(action.endX, screenWidth)
                        val normEndY = normalizeY(action.endY, screenHeight)
                        performSwipeWithCallback(normX, normY, normEndX, normEndY, action.durationMs) {}
                    }
                    else -> Thread.sleep(action.durationMs)
                }

                try {
                    Thread.sleep(action.delayAfterMs)
                } catch (e: InterruptedException) {
                    isRunningState.set(false)
                    isPlaying = false
                    break
                }
            }
        }
    }

    fun performClickSync(x: Int, y: Int, durationMs: Long): Boolean {
        val latch = CountDownLatch(1)
        var result = false
        val path = Path().apply { moveTo(x.toFloat(), y.toFloat()) }
        val stroke = GestureDescription.StrokeDescription(path, 0, durationMs.coerceAtLeast(1L))
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                result = true
                latch.countDown()
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                result = false
                latch.countDown()
            }
        }, null)

        try { latch.await(2, TimeUnit.SECONDS) } catch (e: InterruptedException) { return false }
        return result
    }

    fun performSwipeWithCallback(startX: Int, startY: Int, endX: Int, endY: Int, durationMs: Long, callback: (Boolean) -> Unit) {
        val path = Path().apply {
            moveTo(startX.toFloat(), startY.toFloat())
            lineTo(endX.toFloat(), endY.toFloat())
        }
        val stroke = GestureDescription.StrokeDescription(path, 0, durationMs.coerceAtLeast(10L))
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                vibrateFeedback(20L)
                callback(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) { callback(false) }
        }, null)
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        performSwipeWithCallback(startX.toInt(), startY.toInt(), endX.toInt(), endY.toInt(), durationMs, callback ?: {})
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() { stopExecution() }

    override fun onDestroy() {
        super.onDestroy()
        stopExecution()
        if (instance == this) instance = null
        overlayManager.removeAllTargets()
        executorThread.quitSafely()
    }
}
