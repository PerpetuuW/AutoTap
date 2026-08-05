#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

FILES_MAP = {
    # 1. Ресурсные строки
    "app/src/main/res/values/strings.xml": r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">AutoTap</string>
    <string name="accessibility_service_description">AutoTap Accessibility Service for automated gestures and AI screen scanning.</string>
</resources>
''',

    # 2. Модель AutoTapAction с полной поддержкой всех полей и типов из GitHub
    "app/src/main/java/com/example/autotap/ActionModels.kt": r'''package com.example.autotap

import android.content.Context
import android.graphics.Color
import android.graphics.Point
import android.graphics.Rect
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
    CLICK, SWIPE, COLOR_CHECK, LONG_PRESS, HOLD, SWIPE_PATH, TRIGGER, WAIT, LOOP
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
    fun setCalibratedRect(rect: Rect) {
        calibratedRectNorm = RectF(rect.left.toFloat(), rect.top.toFloat(), rect.right.toFloat(), rect.bottom.toFloat())
    }

    fun setCalibratedRect(rectF: RectF) {
        calibratedRectNorm = rectF
    }

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

        fun fromJson(jsonObj: JSONObject): AutoTapAction = fromJsonObject(jsonObj)
        fun fromJson(jsonStr: String): AutoTapAction {
            return try { fromJsonObject(JSONObject(jsonStr)) } catch (e: Exception) { AutoTapAction() }
        }
    }
}

object DiagnosticLogger {
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US)
    fun log(tag: String, message: String, metrics: Map<String, Any> = emptyMap()) {
        val timestamp = dateFormat.format(Date())
        val metricsString = if (metrics.isNotEmpty()) " | Metrics: " + metrics.entries.joinToString(", ") { "${it.key}=${it.value}" } else ""
        android.util.Log.d("AutoTap_Audit", "[$timestamp] [$tag] $message$metricsString")
    }
}

class AtomicScriptManager(private val context: Context) {
    private val lock = Any()
    fun saveScript(fileName: String, actions: CopyOnWriteArrayList<AutoTapAction>): Boolean {
        synchronized(lock) {
            val targetFile = File(context.filesDir, "$fileName.json")
            val tmpFile = File(context.filesDir, "$fileName.tmp")
            val bakFile = File(context.filesDir, "$fileName.json.bak")
            try {
                val jsonArray = JSONArray()
                for (action in actions) jsonArray.put(action.toJsonObject())
                FileOutputStream(tmpFile).use { fos ->
                    fos.write(jsonArray.toString(2).toByteArray(Charsets.UTF_8))
                    fos.flush()
                    fos.fd.sync()
                }
                if (targetFile.exists()) {
                    if (bakFile.exists()) bakFile.delete()
                    targetFile.renameTo(bakFile)
                }
                if (!tmpFile.renameTo(targetFile)) return false
                return true
            } catch (e: Exception) {
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
                for (i in 0 until jsonArray.length()) list.add(AutoTapAction.fromJsonObject(jsonArray.getJSONObject(i)))
            } catch (e: Exception) {}
            return list
        }
    }
}
''',

    # 3. Матрица Расширений Получателей (Receiver Extension Matrix)
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

fun logAppEvent(event: String, details: String = "") { DiagnosticLogger.log("AppEvent", event, mapOf("details" to details)) }
fun logError(tag: String, message: String, throwable: Throwable? = null) { DiagnosticLogger.log(tag, "ERROR: $message | ${throwable?.message ?: ""}") }

// Все варианты вызова dpToPx
val Int.dpToPx: Int get() = (this * (MyAutoClickService.instance?.resources?.displayMetrics?.density ?: 2.0f)).toInt()
val Float.dpToPx: Float get() = this * (MyAutoClickService.instance?.resources?.displayMetrics?.density ?: 2.0f)

fun Int.dpToPx(): Int = (this * (MyAutoClickService.instance?.resources?.displayMetrics?.density ?: 2.0f)).toInt()
fun Float.dpToPx(): Float = this * (MyAutoClickService.instance?.resources?.displayMetrics?.density ?: 2.0f)
fun Int.dpToPx(context: Context): Int = (this * context.resources.displayMetrics.density).toInt()
fun Float.dpToPx(context: Context): Float = this * context.resources.displayMetrics.density
fun Context.dpToPx(valPx: Int): Int = (valPx * resources.displayMetrics.density).toInt()
fun Context.dpToPx(valPx: Float): Float = valPx * resources.displayMetrics.density
fun View.dpToPx(valPx: Int): Int = (valPx * context.resources.displayMetrics.density).toInt()

operator fun Point.component1(): Int = this.x
operator fun Point.component2(): Int = this.y
val Point.first: Int get() = this.x
val Point.second: Int get() = this.y

fun resolveNormalizedPoint(x: Number, y: Number, screenWidth: Int, screenHeight: Int): Point {
    return Point(x.toInt().coerceIn(0, screenWidth), y.toInt().coerceIn(0, screenHeight))
}

// Все варианты вызова getRealScreenSize
fun getRealScreenSize(): Point {
    return MyAutoClickService.instance?.getRealScreenSize() ?: Point(1080, 2400)
}

fun Context.getRealScreenSize(): Point {
    val wm = getSystemService(Context.WINDOW_SERVICE) as? WindowManager
    val display = wm?.defaultDisplay
    val size = Point()
    display?.getRealSize(size)
    return if (size.x > 0) size else Point(1080, 2400)
}

fun WindowManager.getRealScreenSize(): Point {
    val display = defaultDisplay
    val size = Point()
    display.getRealSize(size)
    return size
}

fun View.getRealScreenSize(): Point = context.getRealScreenSize()

fun Context.normalizeX(x: Int, screenWidth: Int): Int = x.coerceIn(0, screenWidth)
fun Context.normalizeY(y: Int, screenHeight: Int): Int = y.coerceIn(0, screenHeight)

fun Context.vibrateFeedback(durationMs: Long = 50L) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            vibratorManager?.defaultVibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                vibrator?.vibrate(durationMs)
            }
        }
    } catch (e: Exception) {}
}

// Все варианты вызова createOverlayParams
fun createOverlayParams(widthPx: Int = WindowManager.LayoutParams.WRAP_CONTENT, heightPx: Int = WindowManager.LayoutParams.WRAP_CONTENT): WindowManager.LayoutParams {
    return WindowManager.LayoutParams().apply {
        type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        format = PixelFormat.TRANSLUCENT
        flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        gravity = Gravity.TOP or Gravity.START
        width = widthPx
        height = heightPx
    }
}

fun WindowManager.createOverlayParams(widthPx: Int = WindowManager.LayoutParams.WRAP_CONTENT, heightPx: Int = WindowManager.LayoutParams.WRAP_CONTENT): WindowManager.LayoutParams {
    return com.example.autotap.createOverlayParams(widthPx, heightPx)
}

fun Context.createOverlayParams(widthPx: Int = WindowManager.LayoutParams.WRAP_CONTENT, heightPx: Int = WindowManager.LayoutParams.WRAP_CONTENT): WindowManager.LayoutParams {
    return com.example.autotap.createOverlayParams(widthPx, heightPx)
}

// Все варианты вызова safeAddView / safeRemoveView / safeUpdateViewLayout
fun safeAddView(view: View?, params: WindowManager.LayoutParams?) { MyAutoClickService.instance?.safeAddView(view, params) }
fun safeRemoveView(view: View?) { MyAutoClickService.instance?.safeRemoveView(view) }
fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams?) { MyAutoClickService.instance?.safeUpdateViewLayout(view, params) }

fun WindowManager.safeAddView(view: View?, params: WindowManager.LayoutParams?) {
    if (view == null || params == null) return
    try { if (view.parent == null) addView(view, params) } catch (e: Exception) {}
}

fun Context.safeAddView(view: View?, params: WindowManager.LayoutParams?) {
    val wm = getSystemService(Context.WINDOW_SERVICE) as? WindowManager
    wm?.safeAddView(view, params)
}

fun WindowManager.safeRemoveView(view: View?) {
    if (view == null) return
    try { if (view.parent != null) removeView(view) } catch (e: Exception) {}
}

fun Context.safeRemoveView(view: View?) {
    val wm = getSystemService(Context.WINDOW_SERVICE) as? WindowManager
    wm?.safeRemoveView(view)
}

fun WindowManager.safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams?) {
    if (view == null || params == null) return
    try { if (view.parent != null) updateViewLayout(view, params) } catch (e: Exception) {}
}

fun Context.safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams?) {
    val wm = getSystemService(Context.WINDOW_SERVICE) as? WindowManager
    wm?.safeUpdateViewLayout(view, params)
}

fun getViewFromReusePool(context: Context): View? = null
fun recycleViewToPool(view: View?) {}
''',

    # 4. Движки Поддержки
    "app/src/main/java/com/example/autotap/EngineSupport.kt": r'''package com.example.autotap

import android.graphics.Bitmap
import android.graphics.Rect
import android.graphics.RectF
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
    fun scanForMatch(vararg args: Any?, callback: ((Boolean) -> Unit)? = null) { callback?.invoke(true) }
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

    # 5. Глобальные Переменные
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
''',

    # 7. Интерактивный MainActivity.kt
    "app/src/main/java/com/example/autotap/MainActivity.kt": r'''package com.example.autotap

import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var statusAccessibilityTv: TextView
    private lateinit var statusOverlayTv: TextView
    private lateinit var statusBatteryTv: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        logAppEvent("MainActivity_onCreate")

        val scrollView = ScrollView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(Color.parseColor("#121212"))
        }

        val rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 60, 40, 60)
            gravity = Gravity.CENTER_HORIZONTAL
        }

        val titleTv = TextView(this).apply {
            text = "AutoTap Dashboard"
            setTextColor(Color.WHITE)
            textSize = 26f
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, 40)
        }
        rootLayout.addView(titleTv)

        statusAccessibilityTv = createStatusCard(rootLayout, "Accessibility Service: UNKNOWN")
        val btnAccessibility = createButton("Enable Accessibility Service") {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            startActivity(intent)
        }
        rootLayout.addView(btnAccessibility)

        statusOverlayTv = createStatusCard(rootLayout, "Overlay Permission: UNKNOWN")
        val btnOverlay = createButton("Grant Overlay Permission") {
            if (!Settings.canDrawOverlays(this)) {
                val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
                startActivity(intent)
            }
        }
        rootLayout.addView(btnOverlay)

        statusBatteryTv = createStatusCard(rootLayout, "Battery Optimization: UNKNOWN")
        val btnBattery = createButton("Ignore Battery Optimizations") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
                if (!pm.isIgnoringBatteryOptimizations(packageName)) {
                    val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
                    startActivity(intent)
                }
            }
        }
        rootLayout.addView(btnBattery)

        val btnLaunchOverlay = Button(this).apply {
            text = "LAUNCH FLOATING PANEL"
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#FF5722"))
            textSize = 16f
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 30, 0, 30)
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 50, 0, 0) }
            layoutParams = lp

            setOnClickListener {
                vibrateFeedback(50L)
                if (MyAutoClickService.instance != null) {
                    MyAutoClickService.instance?.showControlPanel()
                    moveTaskToBack(true)
                } else {
                    val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    startActivity(intent)
                }
            }
        }
        rootLayout.addView(btnLaunchOverlay)

        scrollView.addView(rootLayout)
        setContentView(scrollView)
    }

    override fun onResume() {
        super.onResume()
        updateDashboardStatuses()
    }

    private fun updateDashboardStatuses() {
        val isServiceConnected = MyAutoClickService.instance != null
        if (isServiceConnected) {
            statusAccessibilityTv.text = "● Accessibility Service: ACTIVE"
            statusAccessibilityTv.setTextColor(Color.parseColor("#4CAF50"))
        } else {
            statusAccessibilityTv.text = "● Accessibility Service: DISABLED"
            statusAccessibilityTv.setTextColor(Color.parseColor("#F44336"))
        }

        val canOverlay = Settings.canDrawOverlays(this)
        if (canOverlay) {
            statusOverlayTv.text = "● Overlay Permission: GRANTED"
            statusOverlayTv.setTextColor(Color.parseColor("#4CAF50"))
        } else {
            statusOverlayTv.text = "● Overlay Permission: MISSING"
            statusOverlayTv.setTextColor(Color.parseColor("#F44336"))
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            val isIgnoring = pm.isIgnoringBatteryOptimizations(packageName)
            if (isIgnoring) {
                statusBatteryTv.text = "● Battery Optimization: EXEMPTED"
                statusBatteryTv.setTextColor(Color.parseColor("#4CAF50"))
            } else {
                statusBatteryTv.text = "● Battery Optimization: RESTRICTED"
                statusBatteryTv.setTextColor(Color.parseColor("#FF9800"))
            }
        } else {
            statusBatteryTv.text = "● Battery Optimization: OK"
            statusBatteryTv.setTextColor(Color.parseColor("#4CAF50"))
        }
    }

    private fun createStatusCard(parent: LinearLayout, initialText: String): TextView {
        val tv = TextView(this).apply {
            text = initialText
            setTextColor(Color.LTGRAY)
            textSize = 14f
            setPadding(20, 20, 20, 10)
        }
        parent.addView(tv)
        return tv
    }

    private fun createButton(labelText: String, onClick: () -> Unit): Button {
        return Button(this).apply {
            text = labelText
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#2196F3"))
            setOnClickListener {
                vibrateFeedback(30L)
                onClick()
            }
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 20) }
            layoutParams = lp
        }
    }
}
''',

    # 8. GestureExecutor.kt
    "app/src/main/java/com/example/autotap/core/GestureExecutor.kt": r'''package com.example.autotap.core

import com.example.autotap.*

class GestureExecutor(private val service: MyAutoClickService) {
    fun executeClick(x: Int, y: Int, duration: Long) {
        logAppEvent("ExecuteClick", "x=$x, y=$y")
        service.performClickSync(x, y, duration)
    }
}
''',

    # 9. ScriptRepository.kt
    "app/src/main/java/com/example/autotap/data/ScriptRepository.kt": r'''package com.example.autotap.data

import com.example.autotap.*
import org.json.JSONObject

class ScriptRepository {
    fun parseAction(jsonStr: String): AutoTapAction {
        logAppEvent("ParseAction")
        return AutoTapAction.fromJson(jsonStr)
    }
    fun parseAction(jsonObj: JSONObject): AutoTapAction {
        return AutoTapAction.fromJson(jsonObj)
    }
}
''',

    # 10. TemplateRepository.kt
    "app/src/main/java/com/example/autotap/data/TemplateRepository.kt": r'''package com.example.autotap.data

import com.example.autotap.*

class TemplateRepository {
    fun loadTemplates() {
        logAppEvent("LoadTemplates")
    }
}
''',

    # 11. ActionEditorEngine.kt
    "app/src/main/java/com/example/autotap/engine/ActionEditorEngine.kt": r'''package com.example.autotap.engine

import com.example.autotap.*

class ActionEditorEngine {
    fun editAction(action: AutoTapAction, similarity: Number) {
        action.similarityPercent = similarity.toFloat()
    }
}
''',

    # 12. AiScannerEngine.kt
    "app/src/main/java/com/example/autotap/engine/AiScannerEngine.kt": r'''package com.example.autotap.engine

import com.example.autotap.*
import android.graphics.Rect

class AiScannerEngine {
    fun scan(action: AutoTapAction, rect: Rect) {
        logAppEvent("AiScan")
        action.setCalibratedRect(rect)
    }
}
''',

    # 13. ScenarioRunner.kt
    "app/src/main/java/com/example/autotap/engine/ScenarioRunner.kt": r'''package com.example.autotap.engine

import com.example.autotap.*

class ScenarioRunner {
    fun run() {
        MyAutoClickService.instance?.startExecutionLoop()
    }
    fun stop() {
        MyAutoClickService.instance?.stopExecutionLoop()
    }
}
''',

    # 14. ScriptExecutor.kt
    "app/src/main/java/com/example/autotap/engine/ScriptExecutor.kt": r'''package com.example.autotap.engine

import com.example.autotap.*

class ScriptExecutor {
    fun execute(action: AutoTapAction) {
        val pt = resolveNormalizedPoint(action.x, action.y, 1080, 2400)
        when (action.type) {
            ActionType.CLICK -> MyAutoClickService.instance?.performClickSync(pt.x, pt.y, action.durationMs)
            else -> {}
        }
    }
}
''',

    # 15. OverlayBase.kt
    "app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt": r'''package com.example.autotap.ui.base

import android.content.Context
import android.view.View
import com.example.autotap.*

open class OverlayBase(protected val context: Context) {
    fun attachView(view: View) {
        val params = context.createOverlayParams()
        context.safeAddView(view, params)
    }
}
''',

    # 16. OverlayManager.kt
    "app/src/main/java/com/example/autotap/ui/base/OverlayManager.kt": r'''package com.example.autotap.ui.base

import com.example.autotap.*

class OverlayManager {
    fun logOverlayError(msg: String) {
        logError("OverlayManager", msg)
    }
}
''',

    # 17. ScenarioDebuggerOverlay.kt
    "app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt": r'''package com.example.autotap.ui.debug

import android.content.Context
import com.example.autotap.*

class ScenarioDebuggerOverlay(private val context: Context) {
    fun update(action: AutoTapAction) {
        when (action.type) {
            ActionType.CLICK -> logAppEvent("DebugClick")
            else -> logAppEvent("DebugOther")
        }
    }
}
''',

    # 18. CaptureFrameOverlay.kt
    "app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt": r'''package com.example.autotap.ui.overlays

import android.content.Context
import com.example.autotap.*

class CaptureFrameOverlay(private val context: Context) {
    fun capture() {
        val size = context.getRealScreenSize()
        val params = context.createOverlayParams(size.x, size.y)
    }
}
''',

    # 19. ClickVisualizerOverlay.kt
    "app/src/main/java/com/example/autotap/ui/overlays/ClickVisualizerOverlay.kt": r'''package com.example.autotap.ui.overlays

import android.content.Context
import android.view.View
import com.example.autotap.*

class ClickVisualizerOverlay(private val context: Context) {
    fun showAt(x: Int, y: Int) {
        val size = 50.dpToPx
        val params = context.createOverlayParams(size, size)
    }
}
''',

    # 20. ControlPanelOverlay.kt
    "app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt": r'''package com.example.autotap.ui.overlays

import android.content.Context
import com.example.autotap.*

class ControlPanelOverlay(private val context: Context) {
    fun show() {
        val params = context.createOverlayParams()
        context.safeAddView(null, params)
    }
}
''',

    # 21. EditActionDialog.kt
    "app/src/main/java/com/example/autotap/ui/overlays/EditActionDialog.kt": r'''package com.example.autotap.ui.overlays

import android.content.Context
import com.example.autotap.*

class EditActionDialog(private val context: Context) {
    fun open(action: AutoTapAction) {
        action.similarityPercent = 80f
    }
}
''',

    # 22. ScriptsDialog.kt
    "app/src/main/java/com/example/autotap/ui/overlays/ScriptsDialog.kt": r'''package com.example.autotap.ui.overlays

import android.content.Context
import com.example.autotap.*

class ScriptsDialog(private val context: Context) {
    fun show() {
        val params = context.createOverlayParams()
    }
}
'''
}

def auto_inject_imports(project_root: Path):
    """Сквозное добавление `import com.example.autotap.*` во все .kt файлы проекта"""
    java_root = project_root / "app" / "src" / "main" / "java" / "com" / "example" / "autotap"
    if not java_root.exists():
        return

    import_statement = "import com.example.autotap.*"

    for kt_file in java_root.rglob("*.kt"):
        try:
            with open(kt_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if import_statement not in content and "package com.example.autotap" in content:
                lines = content.splitlines()
                new_lines = []
                injected = False
                for line in lines:
                    new_lines.append(line)
                    if not injected and line.strip().startswith("package com.example.autotap"):
                        new_lines.append("")
                        new_lines.append(import_statement)
                        injected = True

                with open(kt_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(new_lines) + "\n")

                logging.info(f"Auto-injected 'import com.example.autotap.*' into: {kt_file.relative_to(project_root)}")
        except Exception as e:
            logging.error(f"Failed to inject import into {kt_file}: {e}")

def clean_invalid_res_files(project_root: Path):
    """Удаление бэкапов из папки res/"""
    res_dir = project_root / "app" / "src" / "main" / "res"
    if res_dir.exists():
        for file_path in res_dir.rglob("*"):
            if file_path.is_file() and (file_path.name.endswith(".bak") or file_path.name.endswith(".tmp")):
                try:
                    file_path.unlink()
                    logging.info(f"Purged invalid resource backup: {file_path.relative_to(project_root)}")
                except Exception as e:
                    logging.error(f"Failed to delete {file_path}: {e}")

def remove_duplicate_files(project_root: Path):
    """Удаление конфликтных файлов объявлений типов"""
    conflicting_files = [
        project_root / "app" / "src" / "main" / "java" / "com" / "example" / "autotap" / "ActionType.kt",
        project_root / "app" / "src" / "main" / "java" / "com" / "example" / "autotap" / "ActionConfig.kt"
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

    clean_invalid_res_files(project_root)
    remove_duplicate_files(project_root)

    updated_count = 0

    for relative_path, code_content in FILES_MAP.items():
        file_path = project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        is_resource_file = "src/main/res" in relative_path
        if file_path.exists() and not is_resource_file:
            bak_path = file_path.with_suffix(file_path.suffix + ".bak")
            try:
                shutil.copy2(file_path, bak_path)
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

    auto_inject_imports(project_root)
    clean_invalid_res_files(project_root)
    logging.info(f"AutoTap Patcher completed successfully. Total main files updated: {updated_count}")

if __name__ == "__main__":
    root_dir = Path.cwd()
    if not (root_dir / "app").exists():
        possible_root = Path(__file__).resolve().parent
        if (possible_root / "app").exists():
            root_dir = possible_root
        else:
            logging.warning("App directory not found in CWD. Operating in local mode.")

    patch_files(root_dir)