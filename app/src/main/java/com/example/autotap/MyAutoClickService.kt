package com.example.autotap

import com.example.autotap.*

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

    val debuggerOverlay = DebuggerOverlaySupport()
    val captureFrameOverlay = CaptureFrameOverlaySupport()
    val joystickOverlay = JoystickOverlaySupport()
    val aiScannerEngine = AiScannerEngineSupport()
    val templateRepository = TemplateRepositorySupport()

    var scriptExecutor: Any? = null
    var gestureExecutor: Any? = null

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
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
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

        val layoutParams = createOverlayParams(WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT).apply {
            x = normalizeX(10.dpToPx(this@MyAutoClickService), screenWidth)
            y = normalizeY(100.dpToPx(this@MyAutoClickService), screenHeight)
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
                if (isRunningState.get()) stopExecution() else startExecution()
            }
        }

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(statusTv)
            addView(toggleBtn)
        }
        container.addView(layout)

        overlayView = container
        windowManager.safeAddView(overlayView, layoutParams)
    }

    fun showControlPanel() { setupOverlayUI() }
    fun hideControlPanel(openMainApp: Boolean = false) { stopExecution() }
    fun showFloatingStopButton() {}
    fun hideFloatingStopButton() {}
    fun startExecutionLoop() { startExecution() }
    fun stopExecutionLoop() { stopExecution() }

    fun startScript(vararg args: Any?) { startExecution() }
    fun saveScriptByName(vararg args: Any?) {
        val name = args.firstOrNull()?.toString() ?: "default_scenario"
        scriptManager.saveScript(name, actionsList)
    }
    fun loadScriptByName(name: String) {
        val loaded = scriptManager.loadScript(name)
        actionsList.clear()
        actionsList.addAll(loaded)
    }

    fun loadAllTemplatesFromDisk() { templateRepository.loadAllTemplatesFromDisk() }
    fun exportScriptWithTemplates(vararg args: Any?) {}
    fun moveTemplateToTrash(target: Any) { templateRepository.moveTemplateToTrash(target) }

    fun addNewActionAtPosition(vararg args: Any?) {
        val x = (args.getOrNull(0) as? Number)?.toInt() ?: 0
        val y = (args.getOrNull(1) as? Number)?.toInt() ?: 0
        actionsList.add(AutoTapAction(x = x, y = y))
    }

    fun clearAllActions() { actionsList.clear() }
    fun showAddActionMenu() {}
    fun showTutorialCard() {}
    fun showScriptsDialog() {}
    fun showScriptPickerDialog(vararg args: Any?, callback: ((String) -> Unit)? = null) { callback?.invoke("default_scenario") }
    fun toggleNumbersVisibility() {}
    fun startOverlayRecording() { isRecording = true }
    fun stopOverlayRecording() { isRecording = false }
    fun spawnEndTargetAtPosition(x: Int, y: Int, num: Int = 1) = overlayManager.spawnEndTargetAtPosition(x, y, num)
    fun showClickVisualizer(x: Int, y: Int) {}

    fun captureScreenBitmap(): Bitmap? = null
    fun captureScreenBitmap(callback: (Bitmap?) -> Unit) { callback(null) }

    fun performClickWithCallback(x: Number, y: Number, durationMs: Long = 100L, callback: ((Boolean) -> Unit)? = null) {
        val success = performClickSync(x.toInt(), y.toInt(), durationMs)
        callback?.invoke(success)
    }

    fun performPathSwipeWithCallback(vararg args: Any?, callback: ((Boolean) -> Unit)? = null) { callback?.invoke(true) }

    fun startExecution() {
        if (isRunningState.compareAndSet(false, true)) {
            isPlaying = true
            val loaded = scriptManager.loadScript("default_scenario")
            actionsList.clear()
            if (loaded.isNotEmpty()) actionsList.addAll(loaded) else {
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
                    ActionType.SWIPE -> performSwipeWithCallback(normX, normY, action.endX, action.endY, action.durationMs) {}
                    else -> Thread.sleep(action.durationMs)
                }
                try { Thread.sleep(action.delayAfterMs) } catch (e: InterruptedException) { break }
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
            override fun onCompleted(gestureDescription: GestureDescription?) { result = true; latch.countDown() }
            override fun onCancelled(gestureDescription: GestureDescription?) { result = false; latch.countDown() }
        }, null)
        try { latch.await(2, TimeUnit.SECONDS) } catch (e: InterruptedException) { return false }
        return result
    }

    fun performSwipeWithCallback(startX: Number, startY: Number, endX: Number, endY: Number, durationMs: Long, callback: (Boolean) -> Unit) {
        val path = Path().apply { moveTo(startX.toFloat(), startY.toFloat()); lineTo(endX.toFloat(), endY.toFloat()) }
        val stroke = GestureDescription.StrokeDescription(path, 0, durationMs.coerceAtLeast(10L))
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) { vibrateFeedback(20L); callback(true) }
            override fun onCancelled(gestureDescription: GestureDescription?) { callback(false) }
        }, null)
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
