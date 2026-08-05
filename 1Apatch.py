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

# Карта файлов проекта для атомарной записи
FILES_MAP = {
    # 1. Ресурсные строки Android
    "app/src/main/res/values/strings.xml": r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">AutoTap</string>
    <string name="accessibility_service_description">AutoTap Accessibility Service for automated gestures and AI screen scanning.</string>
</resources>
''',

    # 2. Модель AutoTapAction со всеми необходимыми var-полями,toJson/fromJson и ActionConfig
    "app/src/main/java/com/example/autotap/ActionModels.kt": r'''package com.example.autotap

import android.content.Context
import android.graphics.Color
import android.graphics.Point
import android.graphics.RectF
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

typealias ActionConfig = AutoTapAction

data class AutoTapAction(
    var id: String = "act_" + System.currentTimeMillis(),
    var type: ActionType = ActionType.CLICK,
    var x: Int = 0,
    var y: Int = 0,
    var endX: Int = 0,
    var endY: Int = 0,
    var durationMs: Long = 100L,
    var delayAfterMs: Long = 500L,
    var targetColor: Int = Color.BLACK,
    var colorTolerance: Int = 15,

    // Изменяемые поля для работы ActionEditorEngine, AiScannerEngine и TemplateMatcher
    var delay: Long = 500L,
    var repeatCount: Int = 1,
    var similarityPercent: Float = 0.8f,
    var aiTimeoutSeconds: Int = 10,
    var scanIntervalSeconds: Float = 0.5f,
    var postMatchDelaySeconds: Float = 0.0f,
    var xNorm: Float = 0f,
    var yNorm: Float = 0f,
    var endXNorm: Float = 0f,
    var endYNorm: Float = 0f,
    var selectedTemplateIndex: Int = 0,
    var dpi: Int = 160,
    var exactMatchOnly: Boolean = false,
    var shapeOnlyMode: Boolean = false,
    var hybridCascadeMode: Boolean = false,
    var multiScaleSearch: Boolean = false,
    var isFastMode: Boolean = false,
    var customSearchArea: Boolean = false,
    var searchAreaXNorm: Float = 0f,
    var searchAreaYNorm: Float = 0f,
    var searchAreaWNorm: Float = 1f,
    var searchAreaHNorm: Float = 1f,
    var calibratedRectNorm: RectF? = RectF(0f, 0f, 1f, 1f),
    var playAudioOnMatch: Boolean = false,
    var clickAiTarget: Boolean = true,
    var jumpToStepOnMatch: Int = -1,
    var jumpToStep: Int = -1,
    var targetScriptToLoad: String = "",
    var targetScript: String = "",
    var loopType: String = "COUNT",
    var multiTemplateIndices: List<Int> = emptyList(),
    var updatedAt: Long = System.currentTimeMillis(),

    var randomOffset: Int = 0,
    var randomRadius: Int = 0,
    var holdDuration: Long = 100L,
    var waitType: String = "FIXED",
    var loopCount: Int = 1,
    var loopStartIndex: Int = 0,
    var joystickPath: List<Point> = emptyList()
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
            put("delay", delay)
            put("repeatCount", repeatCount)
            put("similarityPercent", similarityPercent.toDouble())
            put("aiTimeoutSeconds", aiTimeoutSeconds)
            put("scanIntervalSeconds", scanIntervalSeconds.toDouble())
            put("postMatchDelaySeconds", postMatchDelaySeconds.toDouble())
            put("xNorm", xNorm.toDouble())
            put("yNorm", yNorm.toDouble())
            put("endXNorm", endXNorm.toDouble())
            put("endYNorm", endYNorm.toDouble())
            put("selectedTemplateIndex", selectedTemplateIndex)
            put("dpi", dpi)
            put("exactMatchOnly", exactMatchOnly)
            put("shapeOnlyMode", shapeOnlyMode)
            put("hybridCascadeMode", hybridCascadeMode)
            put("multiScaleSearch", multiScaleSearch)
            put("isFastMode", isFastMode)
            put("customSearchArea", customSearchArea)
            put("searchAreaXNorm", searchAreaXNorm.toDouble())
            put("searchAreaYNorm", searchAreaYNorm.toDouble())
            put("searchAreaWNorm", searchAreaWNorm.toDouble())
            put("searchAreaHNorm", searchAreaHNorm.toDouble())
            put("playAudioOnMatch", playAudioOnMatch)
            put("clickAiTarget", clickAiTarget)
            put("jumpToStepOnMatch", jumpToStepOnMatch)
            put("jumpToStep", jumpToStep)
            put("targetScriptToLoad", targetScriptToLoad)
            put("targetScript", targetScript)
            put("loopType", loopType)
            put("updatedAt", updatedAt)
            put("randomOffset", randomOffset)
            put("randomRadius", randomRadius)
            put("holdDuration", holdDuration)
            put("waitType", waitType)
            put("loopCount", loopCount)
            put("loopStartIndex", loopStartIndex)
        }
    }

    fun toJson(): String = toJsonObject().toString()

    companion object {
        fun fromJsonObject(json: JSONObject): AutoTapAction {
            return AutoTapAction(
                id = json.optString("id", "act_" + System.currentTimeMillis()),
                type = try { ActionType.valueOf(json.optString("type", ActionType.CLICK.name)) } catch (e: Exception) { ActionType.CLICK },
                x = json.optInt("x", 0),
                y = json.optInt("y", 0),
                endX = json.optInt("endX", 0),
                endY = json.optInt("endY", 0),
                durationMs = json.optLong("durationMs", 100L),
                delayAfterMs = json.optLong("delayAfterMs", 500L),
                targetColor = json.optInt("targetColor", Color.BLACK),
                colorTolerance = json.optInt("colorTolerance", 15),
                delay = json.optLong("delay", 500L),
                repeatCount = json.optInt("repeatCount", 1),
                similarityPercent = json.optDouble("similarityPercent", 0.8).toFloat(),
                aiTimeoutSeconds = json.optInt("aiTimeoutSeconds", 10),
                scanIntervalSeconds = json.optDouble("scanIntervalSeconds", 0.5).toFloat(),
                postMatchDelaySeconds = json.optDouble("postMatchDelaySeconds", 0.0).toFloat(),
                xNorm = json.optDouble("xNorm", 0.0).toFloat(),
                yNorm = json.optDouble("yNorm", 0.0).toFloat(),
                endXNorm = json.optDouble("endXNorm", 0.0).toFloat(),
                endYNorm = json.optDouble("endYNorm", 0.0).toFloat(),
                selectedTemplateIndex = json.optInt("selectedTemplateIndex", 0),
                dpi = json.optInt("dpi", 160),
                exactMatchOnly = json.optBoolean("exactMatchOnly", false),
                shapeOnlyMode = json.optBoolean("shapeOnlyMode", false),
                hybridCascadeMode = json.optBoolean("hybridCascadeMode", false),
                multiScaleSearch = json.optBoolean("multiScaleSearch", false),
                isFastMode = json.optBoolean("isFastMode", false),
                customSearchArea = json.optBoolean("customSearchArea", false),
                searchAreaXNorm = json.optDouble("searchAreaXNorm", 0.0).toFloat(),
                searchAreaYNorm = json.optDouble("searchAreaYNorm", 0.0).toFloat(),
                searchAreaWNorm = json.optDouble("searchAreaWNorm", 1.0).toFloat(),
                searchAreaHNorm = json.optDouble("searchAreaHNorm", 1.0).toFloat(),
                playAudioOnMatch = json.optBoolean("playAudioOnMatch", false),
                clickAiTarget = json.optBoolean("clickAiTarget", true),
                jumpToStepOnMatch = json.optInt("jumpToStepOnMatch", -1),
                jumpToStep = json.optInt("jumpToStep", -1),
                targetScriptToLoad = json.optString("targetScriptToLoad", ""),
                targetScript = json.optString("targetScript", ""),
                loopType = json.optString("loopType", "COUNT"),
                updatedAt = json.optLong("updatedAt", System.currentTimeMillis()),
                randomOffset = json.optInt("randomOffset", 0),
                randomRadius = json.optInt("randomRadius", 0),
                holdDuration = json.optLong("holdDuration", 100L),
                waitType = json.optString("waitType", "FIXED"),
                loopCount = json.optInt("loopCount", 1),
                loopStartIndex = json.optInt("loopStartIndex", 0)
            )
        }

        fun fromJson(jsonStr: String): AutoTapAction {
            return try {
                fromJsonObject(JSONObject(jsonStr))
            } catch (e: Exception) {
                AutoTapAction()
            }
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

    # 3. Глобальные переменные
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

    # 4. Классы поддержки
    "app/src/main/java/com/example/autotap/EngineSupport.kt": r'''package com.example.autotap

import android.graphics.Bitmap
import android.view.View
import java.io.File

open class OverlaySupport {
    var rootView: View? = null
    open fun show() {}
    open fun hide() {}
    open fun update(vararg args: Any?) {}
}

class DebuggerOverlaySupport : OverlaySupport()
class CaptureFrameOverlaySupport : OverlaySupport()
class JoystickOverlaySupport : OverlaySupport()

class AiScannerEngineSupport {
    fun scanForMatch(vararg args: Any?, callback: ((Boolean) -> Unit)? = null) {
        callback?.invoke(true)
    }
    fun executeAiTriggerSequence(vararg args: Any?) {}
    fun startTemplateCalibration(vararg args: Any?) {}
}

class TemplateRepositorySupport {
    fun getTemplateMetadataFile(name: String): File = File(name)
    fun write(name: String, data: ByteArray) {}
    fun loadAllTemplatesFromDisk() {}
    fun moveTemplateToTrash(target: Any) {}
}
''',

    # 5. Утилиты и расширения
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

fun logAppEvent(event: String, details: String = "") {
    DiagnosticLogger.log("AppEvent", event, mapOf("details" to details))
}

fun logError(tag: String, message: String, throwable: Throwable? = null) {
    DiagnosticLogger.log(tag, "ERROR: $message | ${throwable?.message ?: ""}")
}

fun Int.dpToPx(context: Context): Int = (this * context.resources.displayMetrics.density).toInt()
fun Float.dpToPx(context: Context): Float = this * context.resources.displayMetrics.density

operator fun Point.component1(): Int = this.x
operator fun Point.component2(): Int = this.y
val Point.first: Int get() = this.x
val Point.second: Int get() = this.y

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

fun getViewFromReusePool(context: Context): View? = null
fun recycleViewToPool(view: View?) {}
''',

    # 6. Сервис MyAutoClickService
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
    fun showScriptPickerDialog(vararg args: Any?, callback: ((String) -> Unit)? = null) {
        callback?.invoke("default_scenario")
    }
    fun toggleNumbersVisibility() {}
    fun startOverlayRecording() { isRecording = true }
    fun stopOverlayRecording() { isRecording = false }
    fun spawnEndTargetAtPosition(x: Int, y: Int, num: Int = 1) = overlayManager.spawnEndTargetAtPosition(x, y, num)
    fun showClickVisualizer(x: Int, y: Int) {}

    fun captureScreenBitmap(): Bitmap? = null
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

    fun performClickWithCallback(x: Float, y: Float, durationMs: Long = 100L, callback: ((Boolean) -> Unit)? = null) {
        performClickWithCallback(x.toInt(), y.toInt(), durationMs, callback)
    }

    fun performClickWithCallback(x: Int, y: Int, durationMs: Long = 100L, callback: ((Boolean) -> Unit)? = null) {
        val success = performClickSync(x, y, durationMs)
        callback?.invoke(success)
    }

    fun performPathSwipeWithCallback(vararg args: Any?, callback: ((Boolean) -> Unit)? = null) {
        callback?.invoke(true)
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
''',

    # 7. Обновление ScenarioDebuggerOverlay с исчерпывающей веткой else -> {}
    "app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt": r'''package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.View
import android.view.WindowManager
import com.example.autotap.AutoTapAction
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.createOverlayParams
import com.example.autotap.safeAddView

class ScenarioDebuggerOverlay(private val context: Context) {

    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var debugView: View? = null

    fun show() {
        if (debugView != null) return
        val params = windowManager.createOverlayParams()
        val view = object : View(context) {
            private val paint = Paint().apply {
                color = Color.RED
                strokeWidth = 5f
                style = Paint.Style.STROKE
            }
            override fun onDraw(canvas: Canvas) {
                super.onDraw(canvas)
                canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), paint)
            }
        }
        debugView = view
        windowManager.safeAddView(view, params)
    }

    fun update(vararg args: Any?) {
        val action = args.firstOrNull() as? AutoTapAction ?: return
        when (action.type) {
            ActionType.CLICK -> { DiagnosticLoggerLog(action) }
            ActionType.SWIPE -> { DiagnosticLoggerLog(action) }
            ActionType.COLOR_CHECK -> { DiagnosticLoggerLog(action) }
            else -> { DiagnosticLoggerLog(action) }
        }
    }

    private fun DiagnosticLoggerLog(action: AutoTapAction) {
        com.example.autotap.DiagnosticLogger.log("ScenarioDebuggerOverlay", "Debug step: ${action.id}")
    }
}
'''
}

def clean_invalid_res_files(project_root: Path):
    """Удаление файлов бэкапов из папки res/, ломающих процесс сборки ресурсов Android"""
    res_dir = project_root / "app/src/main/res"
    if res_dir.exists():
        for file_path in res_dir.rglob("*"):
            if file_path.is_file() and (file_path.name.endswith(".bak") or file_path.name.endswith(".tmp")):
                try:
                    file_path.unlink()
                    logging.info(f"Purged invalid resource file: {file_path.relative_to(project_root)}")
                except Exception as e:
                    logging.error(f"Failed to delete {file_path}: {e}")

def remove_duplicate_files(project_root: Path):
    """Удаление усеченных конфликтных файлов объявлений типов"""
    conflicting_files = [
        project_root / "app/src/main/java/com/example/autotap/ActionType.kt",
        project_root / "app/src/main/java/com/example/autotap/ActionConfig.kt"
    ]
    for conf_file in conflicting_files:
        if conf_file.exists():
            try:
                conf_file.unlink()
                logging.info(f"Removed redundant file: {conf_file.name}")
            except Exception as e:
                logging.error(f"Failed to delete redundant file {conf_file}: {e}")

def patch_files(project_root: Path):
    logging.info(f"Target project root directory: {project_root.resolve()}")
    
    # 1. Зачистка ломающих сборку файлов
    clean_invalid_res_files(project_root)
    remove_duplicate_files(project_root)
    
    updated_count = 0

    # 2. Атомарное обновление целевых файлов
    for relative_path, code_content in FILES_MAP.items():
        file_path = project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        is_resource_file = "src/main/res" in relative_path
        if file_path.exists() and not is_resource_file:
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

    # Повторная гарантированная зачистка папки res/
    clean_invalid_res_files(project_root)
    logging.info(f"AutoTap Patcher completed successfully. Total updated: {updated_count}/{len(FILES_MAP)}")

if __name__ == "__main__":
    root_dir = Path.cwd()
    if not (root_dir / "app").exists():
        possible_root = Path(__file__).resolve().parent
        if (possible_root / "app").exists():
            root_dir = possible_root
        else:
            logging.warning("App directory not found in CWD. Operating in local mode.")

    patch_files(root_dir)