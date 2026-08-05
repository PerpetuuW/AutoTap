#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
from pathlib import Path

# Настройка логирования по Регламенту 6
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Карта файлов проекта для атомарной генерации
FILES_MAP = {
    # 1. Исправление ошибки связывания ресурсов Android (Resource Linking Error)
    "app/src/main/res/values/strings.xml": r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">AutoTap</string>
    <string name="accessibility_service_description">AutoTap Accessibility Service for automated taps, gestures, and AI screen scanning.</string>
</resources>
''',

    # 2. Модели данных, расширенный enum ActionType и синонимы типов
    "app/src/main/java/com/example/autotap/ActionModels.kt": r'''package com.example.autotap

import android.content.Context
import android.graphics.Color
import android.graphics.Point
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CopyOnWriteArrayList

enum class ActionType {
    CLICK,
    SWIPE,
    COLOR_CHECK,
    LONG_PRESS,
    HOLD,
    SWIPE_PATH,
    TRIGGER,
    WAIT,
    LOOP
}

// Синоним типа для устранения несоответствий в EditActionDialog
typealias ActionConfig = AutoTapAction

data class AutoTapAction(
    val id: String = "act_" + System.currentTimeMillis(),
    val type: ActionType = ActionType.CLICK,
    val x: Int = 0,
    val y: Int = 0,
    val endX: Int = 0,
    val endY: Int = 0,
    val durationMs: Long = 100L,
    val delayAfterMs: Long = 500L,
    val targetColor: Int = Color.BLACK,
    val colorTolerance: Int = 15,

    // Дополнительные свойства для совместимости со всеми модулями
    val randomOffset: Int = 0,
    val randomRadius: Int = 0,
    val holdDuration: Long = durationMs,
    val waitType: String = "FIXED",
    val loopCount: Int = 1,
    val loopStartIndex: Int = 0,
    val joystickPath: List<Point> = emptyList()
) {
    fun toJsonObject(): JSONObject {
        return JSONObject().apply {
            put("id", id)
            put("type", type.name)
            put("x", x)
            put("y", y)
            put("endX", endX)
            put("endY", endY)
            put("durationMs", durationMs)
            put("delayAfterMs", delayAfterMs)
            put("targetColor", targetColor)
            put("colorTolerance", colorTolerance)
            put("randomOffset", randomOffset)
            put("randomRadius", randomRadius)
            put("holdDuration", holdDuration)
            put("waitType", waitType)
            put("loopCount", loopCount)
            put("loopStartIndex", loopStartIndex)
        }
    }

    companion object {
        fun fromJsonObject(json: JSONObject): AutoTapAction {
            return AutoTapAction(
                id = json.optString("id", "act_" + System.currentTimeMillis()),
                type = ActionType.valueOf(json.optString("type", ActionType.CLICK.name)),
                x = json.optInt("x", 0),
                y = json.optInt("y", 0),
                endX = json.optInt("endX", 0),
                endY = json.optInt("endY", 0),
                durationMs = json.optLong("durationMs", 100L),
                delayAfterMs = json.optLong("delayAfterMs", 500L),
                targetColor = json.optInt("targetColor", Color.BLACK),
                colorTolerance = json.optInt("colorTolerance", 15),
                randomOffset = json.optInt("randomOffset", 0),
                randomRadius = json.optInt("randomRadius", 0),
                holdDuration = json.optLong("holdDuration", 100L),
                waitType = json.optString("waitType", "FIXED"),
                loopCount = json.optInt("loopCount", 1),
                loopStartIndex = json.optInt("loopStartIndex", 0)
            )
        }
    }
}

object DiagnosticLogger {
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US)

    fun log(tag: String, message: String, metrics: Map<String, Any> = emptyMap()) {
        val timestamp = dateFormat.format(Date())
        val metricsString = if (metrics.isNotEmpty()) {
            " | Metrics: " + metrics.entries.joinToString(", ") { "${it.key}=${it.value}" }
        } else {
            ""
        }
        val formattedMessage = "[$timestamp] [$tag] $message$metricsString"
        android.util.Log.d("AutoTap_Audit", formattedMessage)
    }
}

class AtomicScriptManager(private val context: Context) {
    private val lock = Any()

    fun saveScript(fileName: String, actions: CopyOnWriteArrayList<AutoTapAction>): Boolean {
        synchronized(lock) {
            val startTime = System.currentTimeMillis()
            val targetFile = File(context.filesDir, "$fileName.json")
            val tmpFile = File(context.filesDir, "$fileName.tmp")
            val bakFile = File(context.filesDir, "$fileName.json.bak")

            try {
                val jsonArray = JSONArray()
                for (action in actions) {
                    jsonArray.put(action.toJsonObject())
                }
                val jsonString = jsonArray.toString(2)

                FileOutputStream(tmpFile).use { fos ->
                    fos.write(jsonString.toByteArray(Charsets.UTF_8))
                    fos.flush()
                    fos.fd.sync()
                }

                JSONArray(tmpFile.readText(Charsets.UTF_8))

                if (targetFile.exists()) {
                    if (bakFile.exists()) bakFile.delete()
                    targetFile.renameTo(bakFile)
                }

                if (!tmpFile.renameTo(targetFile)) {
                    if (bakFile.exists() && !targetFile.exists()) bakFile.renameTo(targetFile)
                    return false
                }

                DiagnosticLogger.log(
                    "AtomicScriptManager",
                    "Script saved",
                    mapOf("file" to fileName, "durationMs" to (System.currentTimeMillis() - startTime), "count" to actions.size)
                )
                return true
            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Error saving script: ${e.message}")
                if (tmpFile.exists()) tmpFile.delete()
                return false
            }
        }
    }

    fun loadScript(fileName: String): CopyOnWriteArrayList<AutoTapAction> {
        synchronized(lock) {
            val targetFile = File(context.filesDir, "$fileName.json")
            val bakFile = File(context.filesDir, "$fileName.json.bak")
            val fileToRead = when {
                targetFile.exists() && targetFile.length() > 0 -> targetFile
                bakFile.exists() && bakFile.length() > 0 -> bakFile
                else -> null
            }

            val list = CopyOnWriteArrayList<AutoTapAction>()
            if (fileToRead == null) return list

            try {
                val jsonArray = JSONArray(fileToRead.readText(Charsets.UTF_8))
                for (i in 0 until jsonArray.length()) {
                    list.add(AutoTapAction.fromJsonObject(jsonArray.getJSONObject(i)))
                }
            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Error loading script: ${e.message}")
            }
            return list
        }
    }
}
''',

    # 3. Глобальные переменные состояния проекта
    "app/src/main/java/com/example/autotap/GlobalVars.kt": r'''package com.example.autotap

import java.util.concurrent.CopyOnWriteArrayList

var isRecording: Boolean = false
var isPlaying: Boolean = false
var globalClickDurationMs: Long = 100L
var globalScriptLoopCount: Int = 1
var isGlobalScriptInfinite: Boolean = false
var globalRelayNextScript: String = ""

val globalTemplatesNames: MutableList<String> = CopyOnWriteArrayList()
val globalTemplates: MutableList<Any> = CopyOnWriteArrayList()
''',

    # 4. Утилиты, расширения WindowManager, Point и логирования
    "app/src/main/java/com/example/autotap/ExtensionsAndUtils.kt": r'''package com.example.autotap

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.Gravity
import android.view.View
import android.view.WindowManager

// Глобальные методы логирования
fun logAppEvent(event: String, details: String = "") {
    DiagnosticLogger.log("AppEvent", event, mapOf("details" to details))
}

fun logError(tag: String, message: String, throwable: Throwable? = null) {
    DiagnosticLogger.log(tag, "ERROR: $message | ${throwable?.message ?: ""}")
}

// Конвертации размеров
fun Int.dpToPx(context: Context): Int = (this * context.resources.displayMetrics.density).toInt()
fun Float.dpToPx(context: Context): Float = this * context.resources.displayMetrics.density

// Расширения деструктуризации и доступа для Point
operator fun Point.component1(): Int = this.x
operator fun Point.component2(): Int = this.y
val Point.first: Int get() = this.x
val Point.second: Int get() = this.y

// Расчет нормализованной точки
fun resolveNormalizedPoint(x: Int, y: Int, screenWidth: Int, screenHeight: Int): Point {
    return Point(x.coerceIn(0, screenWidth), y.coerceIn(0, screenHeight))
}

fun Context.getRealScreenSize(): Point {
    val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
    val display = wm.defaultDisplay
    val size = Point()
    display.getRealSize(size)
    return size
}

fun Context.normalizeX(x: Int, screenWidth: Int): Int = x.coerceIn(0, screenWidth)
fun Context.normalizeY(y: Int, screenHeight: Int): Int = y.coerceIn(0, screenHeight)

// Потокобезопасный виброотклик
fun Context.vibrateFeedback(durationMs: Long = 50L) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            val vibrator = vibratorManager?.defaultVibrator
            vibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                vibrator?.vibrate(durationMs)
            }
        }
    } catch (e: Exception) {
        DiagnosticLogger.log("VibrateFeedback", "Vibration failed: ${e.message}")
    }
}

// Расширения WindowManager для оверлеев
fun WindowManager.createOverlayParams(widthPx: Int = WindowManager.LayoutParams.WRAP_CONTENT, heightPx: Int = WindowManager.LayoutParams.WRAP_CONTENT): WindowManager.LayoutParams {
    return WindowManager.LayoutParams().apply {
        type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        format = PixelFormat.TRANSLUCENT
        flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        }
        gravity = Gravity.TOP or Gravity.START
        width = widthPx
        height = heightPx
    }
}

fun WindowManager.safeAddView(view: View, params: WindowManager.LayoutParams) {
    try {
        if (view.parent == null) {
            addView(view, params)
        }
    } catch (e: Exception) {
        logError("WindowManager", "safeAddView failed: ${e.message}")
    }
}

fun WindowManager.safeRemoveView(view: View?) {
    if (view == null) return
    try {
        if (view.parent != null) {
            removeView(view)
        }
    } catch (e: Exception) {
        logError("WindowManager", "safeRemoveView failed: ${e.message}")
    }
}

fun WindowManager.safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
    if (view == null) return
    try {
        if (view.parent != null) {
            updateViewLayout(view, params)
        }
    } catch (e: Exception) {
        logError("WindowManager", "safeUpdateViewLayout failed: ${e.message}")
    }
}

// Пул ресурсов оверлей-представлений
fun getViewFromReusePool(context: Context): View? = null
fun recycleViewToPool(view: View?) {}
''',

    # 5. Полная реализация MyAutoClickService со всеми необходимыми ссылками
    "app/src/main/java/com/example/autotap/MyAutoClickService.kt": r'''package com.example.autotap

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
'''
}

def remove_duplicate_files(project_root: Path):
    """Удаление файлов, создающих конфликты переобъявления типы"""
    conflicting_file = project_root / "app/src/main/java/com/example/autotap/ActionType.kt"
    if conflicting_file.exists():
        try:
            conflicting_file.unlink()
            logging.info(f"Removed redundant file: {conflicting_file.name}")
        except Exception as e:
            logging.error(f"Failed to delete {conflicting_file}: {e}")

def patch_files(project_root: Path):
    logging.info(f"Target project root directory: {project_root.resolve()}")
    remove_duplicate_files(project_root)
    updated_count = 0

    for relative_path, code_content in FILES_MAP.items():
        file_path = project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            bak_path = file_path.with_suffix(file_path.suffix + ".bak")
            try:
                shutil.copy2(file_path, bak_path)
                logging.info(f"Backup created: {bak_path.name}")
            except Exception as e:
                logging.error(f"Failed to create backup for {file_path}: {e}")

        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(code_content.strip() + "\n")

            os.replace(tmp_path, file_path)
            updated_count += 1
            logging.info(f"Successfully patched file [100% OK]: {relative_path}")
        except Exception as e:
            logging.error(f"Failed to write file {file_path}: {e}")
            if tmp_path.exists():
                tmp_path.unlink()

    logging.info(f"AutoTap Patcher finished successfully. Total updated: {updated_count}/{len(FILES_MAP)}")

if __name__ == "__main__":
    root_dir = Path.cwd()
    if not (root_dir / "app").exists():
        possible_root = Path(__file__).resolve().parent
        if (possible_root / "app").exists():
            root_dir = possible_root
        else:
            logging.warning("App directory not found in CWD. Using local fallback.")

    patch_files(root_dir)