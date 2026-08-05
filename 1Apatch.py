#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Содержимое исходных файлов Kotlin без сокращений и заглушек
FILES_MAP = {
    "app/src/main/java/com/example/autotap/ActionModels.kt": '''package com.example.autotap

import android.content.Context
import android.graphics.Color
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
    COLOR_CHECK
}

data class AutoTapAction(
    val id: String,
    val type: ActionType,
    val x: Int,
    val y: Int,
    val endX: Int = 0,
    val endY: Int = 0,
    val durationMs: Long = 100L,
    val delayAfterMs: Long = 500L,
    val targetColor: Int = Color.BLACK,
    val colorTolerance: Int = 15
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
        }
    }

    companion object {
        fun fromJsonObject(json: JSONObject): AutoTapAction {
            return AutoTapAction(
                id = json.getString("id"),
                type = ActionType.valueOf(json.getString("type")),
                x = json.getInt("x"),
                y = json.getInt("y"),
                endX = json.optInt("endX", 0),
                endY = json.optInt("endY", 0),
                durationMs = json.optLong("durationMs", 100L),
                delayAfterMs = json.optLong("delayAfterMs", 500L),
                targetColor = json.optInt("targetColor", Color.BLACK),
                colorTolerance = json.optInt("colorTolerance", 15)
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
                    if (bakFile.exists()) {
                        bakFile.delete()
                    }
                    if (!targetFile.renameTo(bakFile)) {
                        DiagnosticLogger.log("AtomicScriptManager", "Failed to backup target file to .bak")
                    }
                }

                if (!tmpFile.renameTo(targetFile)) {
                    DiagnosticLogger.log("AtomicScriptManager", "Failed to rename .tmp to target file")
                    if (bakFile.exists() && !targetFile.exists()) {
                        bakFile.renameTo(targetFile)
                    }
                    return false
                }

                DiagnosticLogger.log(
                    "AtomicScriptManager",
                    "Script saved successfully",
                    mapOf("file" to fileName, "durationMs" to (System.currentTimeMillis() - startTime), "count" to actions.size)
                )
                return true

            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Critical error saving script: ${e.message}")
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
            if (fileToRead == null) {
                DiagnosticLogger.log("AtomicScriptManager", "No valid script file found for: $fileName")
                return list
            }

            try {
                val content = fileToRead.readText(Charsets.UTF_8)
                val jsonArray = JSONArray(content)
                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    list.add(AutoTapAction.fromJsonObject(obj))
                }
                DiagnosticLogger.log("AtomicScriptManager", "Script loaded", mapOf("file" to fileName, "count" to list.size))
            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Error parsing script JSON: ${e.message}")
            }
            return list
        }
    }
}
''',

    "app/src/main/java/com/example/autotap/ExtensionsAndUtils.kt": '''package com.example.autotap

import android.content.Context
import android.graphics.Point
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager

fun Int.dpToPx(context: Context): Int {
    return (this * context.resources.displayMetrics.density).toInt()
}

fun Float.dpToPx(context: Context): Float {
    return this * context.resources.displayMetrics.density
}

operator fun Point.component1(): Int = this.x
operator fun Point.component2(): Int = this.y

fun Context.normalizeX(x: Int, screenWidth: Int): Int {
    return x.coerceIn(0, screenWidth)
}

fun Context.normalizeY(y: Int, screenHeight: Int): Int {
    return y.coerceIn(0, screenHeight)
}

fun Context.vibrateFeedback(durationMs: Long = 50L) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VibratorManagerService) as VibratorManager
            val vibrator = vibratorManager.defaultVibrator
            vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(durationMs)
            }
        }
    } catch (e: Exception) {
        DiagnosticLogger.log("VibrateFeedback", "Vibration failed: ${e.message}")
    }
}
''',

    "app/src/main/java/com/example/autotap/OverlayManager.kt": '''package com.example.autotap

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView

class OverlayManager(private val context: Context) {

    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private val activeTargetViews = mutableListOf<View>()

    private fun createBaseLayoutParams(x: Int, y: Int): WindowManager.LayoutParams {
        return WindowManager.LayoutParams().apply {
            type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
            
            this.gravity = Gravity.TOP or Gravity.START
            this.x = x
            this.y = y
            this.width = 48.dpToPx(context)
            this.height = 48.dpToPx(context)
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    fun spawnEndTargetAtPosition(x: Int, y: Int, targetNumber: Int): View {
        val layoutParams = createBaseLayoutParams(x, y)

        val targetContainer = FrameLayout(context).apply {
            setBackgroundColor(Color.argb(180, 255, 87, 34))
        }

        val label = TextView(context).apply {
            text = "E$targetNumber"
            setTextColor(Color.WHITE)
            textSize = 12f
            gravity = Gravity.CENTER
        }
        targetContainer.addView(label)

        targetContainer.setOnTouchListener(object : View.OnTouchListener {
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
                        context.vibrateFeedback(30L)
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        layoutParams.x = initialX + (event.rawX - touchX).toInt()
                        layoutParams.y = initialY + (event.rawY - touchY).toInt()
                        windowManager.updateViewLayout(targetContainer, layoutParams)
                        return true
                    }
                }
                return false
            }
        })

        windowManager.addView(targetContainer, layoutParams)
        activeTargetViews.add(targetContainer)
        DiagnosticLogger.log("OverlayManager", "Spawned target E$targetNumber at ($x, $y)")
        return targetContainer
    }

    fun removeAllTargets() {
        for (view in activeTargetViews) {
            try {
                windowManager.removeView(view)
            } catch (e: Exception) {
                DiagnosticLogger.log("OverlayManager", "Error removing view: ${e.message}")
            }
        }
        activeTargetViews.clear()
    }
}
''',

    "app/src/main/java/com/example/autotap/MyAutoClickService.kt": '''package com.example.autotap

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

    internal val actionsList = CopyOnWriteArrayList<AutoTapAction>()
    internal lateinit var overlayManager: OverlayManager

    private lateinit var windowManager: WindowManager
    private var overlayView: View? = null
    private var statusTextView: TextView? = null

    private val isRunning = AtomicBoolean(false)
    private lateinit var scriptManager: AtomicScriptManager
    private lateinit var executorThread: HandlerThread
    private lateinit var executorHandler: Handler
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        scriptManager = AtomicScriptManager(this)
        overlayManager = OverlayManager(this)
        executorThread = HandlerThread("AutoTapExecutorThread").apply { start() }
        executorHandler = Handler(executorThread.looper)
        DiagnosticLogger.log("MyAutoClickService", "Service onCreate executed")
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        DiagnosticLogger.log("MyAutoClickService", "Accessibility Service Connected")
        checkBatteryOptimizations()
        setupOverlayUI()
    }

    private fun checkBatteryOptimizations() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(PowerManager::class.java)
            if (pm != null && !pm.isIgnoringBatteryOptimizations(packageName)) {
                DiagnosticLogger.log("MyAutoClickService", "Requesting ignore battery optimizations")
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
                if (isRunning.get()) {
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

    fun startExecution() {
        if (isRunning.compareAndSet(false, true)) {
            val loaded = scriptManager.loadScript("default_scenario")
            actionsList.clear()
            if (loaded.isNotEmpty()) {
                actionsList.addAll(loaded)
            } else {
                val (screenWidth, screenHeight) = getRealScreenSize()
                actionsList.add(
                    AutoTapAction(
                        id = "action_1",
                        type = ActionType.CLICK,
                        x = screenWidth / 2,
                        y = screenHeight / 2
                    )
                )
            }

            mainHandler.post { statusTextView?.text = "Status: RUNNING" }
            executorHandler.post { runExecutionLoop() }
        }
    }

    fun stopExecution() {
        if (isRunning.compareAndSet(true, false)) {
            mainHandler.post { statusTextView?.text = "Status: STOPPED" }
        }
    }

    private fun runExecutionLoop() {
        val (screenWidth, screenHeight) = getRealScreenSize()

        while (isRunning.get()) {
            for (action in actionsList) {
                if (!isRunning.get()) break

                val normX = normalizeX(action.x, screenWidth)
                val normY = normalizeY(action.y, screenHeight)

                when (action.type) {
                    ActionType.CLICK -> {
                        performClickSync(normX, normY, action.durationMs)
                    }
                    ActionType.SWIPE -> {
                        val normEndX = normalizeX(action.endX, screenWidth)
                        val normEndY = normalizeY(action.endY, screenHeight)
                        performSwipeWithCallback(normX, normY, normEndX, normEndY, action.durationMs) { success ->
                            DiagnosticLogger.log("MyAutoClickService", "Swipe status: $success")
                        }
                    }
                    ActionType.COLOR_CHECK -> {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                            performColorCheckSync(action)
                        }
                    }
                }

                try {
                    Thread.sleep(action.delayAfterMs)
                } catch (e: InterruptedException) {
                    isRunning.set(false)
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

        try {
            latch.await(2, TimeUnit.SECONDS)
        } catch (e: InterruptedException) {
            return false
        }
        return result
    }

    fun performSwipeWithCallback(
        startX: Int,
        startY: Int,
        endX: Int,
        endY: Int,
        durationMs: Long,
        callback: (Boolean) -> Unit
    ) {
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

            override fun onCancelled(gestureDescription: GestureDescription?) {
                callback(false)
            }
        }, null)
    }

    fun performSwipeWithCallback(
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        durationMs: Long,
        callback: ((Boolean) -> Unit)? = null
    ) {
        performSwipeWithCallback(
            startX.toInt(),
            startY.toInt(),
            endX.toInt(),
            endY.toInt(),
            durationMs,
            callback ?: {}
        )
    }

    fun performSwipeWithCallback(
        startX: Int,
        startY: Int,
        endX: Int,
        endY: Int,
        durationMs: Long
    ) {
        performSwipeWithCallback(startX, startY, endX, endY, durationMs, {})
    }

    @RequiresApi(Build.VERSION_CODES.R)
    private fun performColorCheckSync(action: AutoTapAction): Boolean {
        val latch = CountDownLatch(1)
        var isMatch = false

        takeScreenshot(
            android.view.Display.DEFAULT_DISPLAY,
            applicationContext.mainExecutor,
            object : TakeScreenshotCallback {
                override fun onSuccess(screenshotResult: ScreenshotResult) {
                    try {
                        val hardwareBuffer = screenshotResult.hardwareBuffer
                        val colorSpace = screenshotResult.colorSpace
                        val bitmap = Bitmap.wrapHardwareBuffer(hardwareBuffer, colorSpace)
                            ?.copy(Bitmap.Config.ARGB_8888, false)

                        hardwareBuffer.close()

                        if (bitmap != null) {
                            if (action.x in 0 until bitmap.width && action.y in 0 until bitmap.height) {
                                val pixel = bitmap.getPixel(action.x, action.y)
                                if (Color.alpha(pixel) >= 30) {
                                    val r1 = Color.red(pixel)
                                    val g1 = Color.green(pixel)
                                    val b1 = Color.blue(pixel)

                                    val r2 = Color.red(action.targetColor)
                                    val g2 = Color.green(action.targetColor)
                                    val b2 = Color.blue(action.targetColor)

                                    isMatch = Math.abs(r1 - r2) <= action.colorTolerance &&
                                              Math.abs(g1 - g2) <= action.colorTolerance &&
                                              Math.abs(b1 - b2) <= action.colorTolerance
                                }
                            }
                            bitmap.recycle()
                        }
                    } catch (e: Exception) {
                        DiagnosticLogger.log("MyAutoClickService", "ColorCheck error: ${e.message}")
                    } finally {
                        latch.countDown()
                    }
                }

                override fun onFailure(errorCode: Int) {
                    latch.countDown()
                }
            }
        )

        try {
            latch.await(3, TimeUnit.SECONDS)
        } catch (e: InterruptedException) {
            return false
        }
        return isMatch
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event?.let {
            if (it.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
                DiagnosticLogger.log("MyAutoClickService", "WindowStateChanged: ${it.packageName}")
            }
        }
    }

    override fun onInterrupt() {
        stopExecution()
    }

    override fun onDestroy() {
        super.onDestroy()
        stopExecution()
        overlayManager.removeAllTargets()
        if (overlayView != null) {
            try {
                windowManager.removeView(overlayView)
            } catch (e: Exception) {
                DiagnosticLogger.log("MyAutoClickService", "Destroy overlay error: ${e.message}")
            }
        }
        executorThread.quitSafely()
    }
}
''',

    "app/src/main/java/com/example/autotap/ui/overlays/JoystickOverlay.kt": '''package com.example.autotap.ui.overlays

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.DiagnosticLogger
import com.example.autotap.MyAutoClickService
import com.example.autotap.dpToPx
import com.example.autotap.vibrateFeedback
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

class JoystickView(context: Context) : View(context) {

    private val outerRadius = 80f
    private val innerRadius = 35f

    private var centerX = 0f
    private var centerY = 0f
    private var handleX = 0f
    private var handleY = 0f

    private val outerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(150, 50, 50, 50)
        style = Paint.Style.FILL
    }

    private val innerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(230, 255, 87, 34)
        style = Paint.Style.FILL
    }

    var onMoveListener: ((deltaX: Float, deltaY: Float) -> Unit)? = null

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        centerX = w / 2f
        centerY = h / 2f
        handleX = centerX
        handleY = centerY
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawCircle(centerX, centerY, outerRadius, outerPaint)
        canvas.drawCircle(handleX, handleY, innerRadius, innerPaint)
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.action) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                val dx = event.x - centerX
                val dy = event.y - centerY
                val distance = sqrt((dx * dx + dy * dy).toDouble()).toFloat()

                if (distance < outerRadius) {
                    handleX = event.x
                    handleY = event.y
                } else {
                    val angle = atan2(dy.toDouble(), dx.toDouble())
                    handleX = (centerX + cos(angle) * outerRadius).toFloat()
                    handleY = (centerY + sin(angle) * outerRadius).toFloat()
                }

                invalidate()
                val normalizedDx = (handleX - centerX) / outerRadius
                val normalizedDy = (handleY - centerY) / outerRadius
                onMoveListener?.invoke(normalizedDx, normalizedDy)
                return true
            }

            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                handleX = centerX
                handleY = centerY
                invalidate()
                onMoveListener?.invoke(0f, 0f)
                return true
            }
        }
        return super.onTouchEvent(event)
    }
}

class JoystickOverlay(
    private val context: Context,
    private val service: MyAutoClickService
) {
    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var overlayView: View? = null

    @SuppressLint("ClickableViewAccessibility")
    fun show() {
        if (overlayView != null) return

        val layoutParams = WindowManager.LayoutParams().apply {
            type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }

            gravity = Gravity.BOTTOM or Gravity.START
            x = 30.dpToPx(context)
            y = 100.dpToPx(context)
            width = 200.dpToPx(context)
            height = 200.dpToPx(context)
        }

        val joystick = JoystickView(context)
        joystick.onMoveListener = { deltaX, deltaY ->
            if (deltaX != 0f || deltaY != 0f) {
                val screenSize = service.getRealScreenSize()
                val startX = screenSize.x / 2f
                val startY = screenSize.y / 2f
                val endX = startX + deltaX * 200f
                val endY = startY + deltaY * 200f

                service.performSwipeWithCallback(
                    startX = startX,
                    startY = startY,
                    endX = endX,
                    endY = endY,
                    durationMs = 80L
                ) { success ->
                    DiagnosticLogger.log(
                        "JoystickOverlay",
                        "Joystick gesture step sent",
                        mapOf("dx" to deltaX, "dy" to deltaY, "success" to success)
                    )
                }
            }
        }

        overlayView = joystick
        windowManager.addView(overlayView, layoutParams)
        context.vibrateFeedback(30L)
        DiagnosticLogger.log("JoystickOverlay", "Joystick overlay attached")
    }

    fun dismiss() {
        overlayView?.let { view ->
            try {
                windowManager.removeView(view)
                DiagnosticLogger.log("JoystickOverlay", "Joystick overlay removed")
            } catch (e: Exception) {
                DiagnosticLogger.log("JoystickOverlay", "Error dismissing joystick overlay: ${e.message}")
            } finally {
                overlayView = null
            }
        }
    }
}
'''
}

def patch_files(project_root: Path):
    logging.info(f"Target project root directory: {project_root.resolve()}")
    updated_count = 0

    for relative_path, code_content in FILES_MAP.items():
        file_path = project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Атомарное бэкапирование старого файла (строгий Python-синтаксис)
        if file_path.exists():
            bak_path = file_path.with_suffix(file_path.suffix + ".bak")
            try:
                shutil.copy2(file_path, bak_path)
                logging.info(f"Backup created: {bak_path.name}")
            except Exception as e:
                logging.error(f"Failed to create backup for {file_path}: {e}")

        # 2. Атомарная запись через .tmp
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

    logging.info(f"AutoTap Patcher completed. Total files updated: {updated_count}/{len(FILES_MAP)}")

if __name__ == "__main__":
    root_dir = Path.cwd()
    if not (root_dir / "app").exists():
        possible_root = Path(__file__).resolve().parent
        if (possible_root / "app").exists():
            root_dir = possible_root
        else:
            logging.warning("App directory not found in CWD. Operating in local mode.")

    patch_files(root_dir)