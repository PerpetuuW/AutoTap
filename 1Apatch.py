#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ast

# -----------------------------------------------------------------------------
# 1. PYTHON SELF-SYNTAX VALIDATOR GUARD (ast.parse)
# -----------------------------------------------------------------------------
def validate_python_self_syntax():
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print("[✓] AST Self-Syntax Validation: Python code syntax is valid.")
    except Exception as e:
        print(f"[💥] CRITICAL PYTHON SYNTAX ERROR in patch script: {e}")
        sys.exit(1)

validate_python_self_syntax()

# -----------------------------------------------------------------------------
# 2. DEFINITIONS OF UPDATED FILES (V54 PROPERTY DECLARATION FIX)
# -----------------------------------------------------------------------------

FILES_TO_PATCH = {}

# FILE 1: MyAutoClickService.kt (Added var globalPreScreenshotDelayMs)
FILES_TO_PATCH["app/src/main/java/com/example/autotap/MyAutoClickService.kt"] = '''package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityService.ScreenshotResult
import android.accessibilityservice.AccessibilityService.TakeScreenshotCallback
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.content.res.Configuration
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorSpace
import android.graphics.PointF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Display
import android.view.accessibility.AccessibilityEvent
import android.widget.Toast
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.GestureExecutor
import com.example.autotap.engine.RecordingEngine
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.engine.TutorialEngine
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.model.ActionConfig
import com.example.autotap.ui.base.OverlayManager
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class MyAutoClickService : AccessibilityService() {

    companion object {
        @Volatile var instance: MyAutoClickService? = null
    }

    val actionsList = mutableListOf<ActionConfig>()
    @Volatile var isPlaying = false

    // 💥 ВОССТАНОВЛЕННЫЕ ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ
    var globalClickDurationMs: Long = 120L
    var globalSwipeDurationMs: Long = 300L
    var globalPreScreenshotDelayMs: Long = 250L

    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var recordingEngine: RecordingEngine
    lateinit var tutorialEngine: TutorialEngine
    lateinit var scriptRepository: ScriptRepository
    lateinit var templateRepository: TemplateRepository
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var overlayManager: OverlayManager

    private val mainHandler = Handler(Looper.getMainLooper())
    private val bgScannerExecutor = Executors.newSingleThreadExecutor()
    private val gestureQueue = ConcurrentLinkedQueue<GestureTask>()
    @Volatile private var isExecutingGesture = false

    data class GestureTask(
        val stroke: GestureDescription.StrokeDescription,
        val description: String,
        val callback: ((Boolean) -> Unit)?
    )

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        StructuredLogger.init(this)

        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        recordingEngine = RecordingEngine(this)
        tutorialEngine = TutorialEngine(this)
        scriptRepository = ScriptRepository(this)
        templateRepository = TemplateRepository(this)
        aiScannerEngine = AiScannerEngine(this)
        overlayManager = OverlayManager(this)

        StructuredLogger.logDiagnostic("SERVICE", "Служба Спец. возможностей подключена и инициализирована.")
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        StructuredLogger.logDiagnostic("SYSTEM", "Смена конфигурации экрана.")
        if (::overlayManager.isInitialized) {
            overlayManager.onConfigurationChanged()
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {
        StructuredLogger.logError("SERVICE", "Служба Accessibility прервана системой.", null)
        gestureQueue.clear()
        isExecutingGesture = false
    }

    override fun onDestroy() {
        super.onDestroy()
        StructuredLogger.logDiagnostic("SERVICE", "Служба Accessibility уничтожена.")
        if (instance == this) {
            instance = null
        }
        bgScannerExecutor.shutdown()
    }

    fun isOverlayArea(x: Float, y: Float): Boolean {
        if (!::overlayManager.isInitialized) return false
        val ptX = x.toInt()
        val ptY = y.toInt()

        if (overlayManager.controlPanel.isShowing && overlayManager.controlPanel.getBounds().contains(ptX, ptY)) return true
        if (overlayManager.joystickOverlay.isShowing && overlayManager.joystickOverlay.getBounds().contains(ptX, ptY)) return true
        if (overlayManager.debuggerOverlay.isShowing && overlayManager.debuggerOverlay.getBounds().contains(ptX, ptY)) return true

        return false
    }

    fun dispatchGestureTask(stroke: GestureDescription.StrokeDescription, description: String, callback: ((Boolean) -> Unit)?) {
        gestureQueue.add(GestureTask(stroke, description, callback))
        processNextGesture()
    }

    private fun processNextGesture() {
        if (isExecutingGesture) return
        val task = gestureQueue.poll() ?: return
        isExecutingGesture = true

        val builder = GestureDescription.Builder()
        builder.addStroke(task.stroke)
        val gesture = builder.build()

        val resultCallback = object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                isExecutingGesture = false
                StructuredLogger.logDiagnostic("GESTURE", "Жест успешно выполнен: " + task.description)
                task.callback?.invoke(true)
                mainHandler.post { processNextGesture() }
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                isExecutingGesture = false
                StructuredLogger.logError("GESTURE", "Жест отменен системой: " + task.description, null)
                task.callback?.invoke(false)
                mainHandler.post { processNextGesture() }
            }
        }

        val dispatched = dispatchGesture(gesture, resultCallback, mainHandler)
        if (!dispatched) {
            isExecutingGesture = false
            StructuredLogger.logError("GESTURE", "Не удалось отправить жест в ОС: " + task.description, null)
            task.callback?.invoke(false)
            mainHandler.post { processNextGesture() }
        }
    }

    fun resolveNormalizedPoint(xNorm: Float, yNorm: Float): PointF {
        val metrics = resources.displayMetrics
        return PointF(xNorm * metrics.widthPixels, yNorm * metrics.heightPixels)
    }

    fun vibrateFeedback(durationMs: Long = 30L) {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                getSystemService(Vibrator::class.java)
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            } ?: return

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(durationMs)
            }
        } catch (e: Exception) {
            StructuredLogger.logError("ERROR", "Ошибка обратной связи вибрации", e)
        }
    }

    fun addNewActionAtPosition(xNorm: Float, yNorm: Float) {
        actionsList.add(ActionConfig(xNorm = xNorm, yNorm = yNorm))
        if (::recordingEngine.isInitialized && recordingEngine.isRecording) {
            recordingEngine.recordClick(xNorm, yNorm)
        }
        StructuredLogger.logDiagnostic("SCRIPT", "Добавлено новое действие на позиции (" + xNorm + ", " + yNorm + ")")
    }

    fun getSafeScriptRepository(): ScriptRepository {
        return if (::scriptRepository.isInitialized) {
            scriptRepository
        } else {
            ScriptRepository(this).also { scriptRepository = it }
        }
    }

    fun getSafeTemplateRepository(): TemplateRepository {
        return if (::templateRepository.isInitialized) {
            templateRepository
        } else {
            TemplateRepository(this).also { templateRepository = it }
        }
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        getSafeScriptRepository().saveScript(name, actions)
    }

    fun loadScriptByName(name: String): Boolean {
        val loaded = getSafeScriptRepository().loadScript(name)
        if (loaded.isNotEmpty()) {
            actionsList.clear()
            actionsList.addAll(loaded)
            return true
        }
        return false
    }

    fun captureScreenBitmapAsync(callback: (Bitmap?) -> Unit) {
        val delay = globalPreScreenshotDelayMs.coerceAtLeast(100L)
        StructuredLogger.logDiagnostic("SCREEN_CAPTURE", "Подготовка к снятию кадра (пауза " + delay + "ms)...")
        mainHandler.postDelayed({
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    takeScreenshot(
                        Display.DEFAULT_DISPLAY,
                        bgScannerExecutor,
                        object : TakeScreenshotCallback {
                            override fun onSuccess(screenshotResult: ScreenshotResult) {
                                val hwBuffer = screenshotResult.hardwareBuffer
                                try {
                                    val cs = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                                        screenshotResult.colorSpace ?: ColorSpace.get(ColorSpace.Named.SRGB)
                                    } else null

                                    val hwBitmap = if (cs != null) {
                                        Bitmap.wrapHardwareBuffer(hwBuffer, cs)
                                    } else {
                                        Bitmap.wrapHardwareBuffer(hwBuffer, ColorSpace.get(ColorSpace.Named.SRGB))
                                    }

                                    val softwareBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, false)

                                    if (softwareBitmap != null) {
                                        StructuredLogger.logDiagnostic("SCREEN_CAPTURE", "Скриншот успешно получен (" + softwareBitmap.width + "x" + softwareBitmap.height + "px)")
                                        callback(softwareBitmap)
                                    } else {
                                        StructuredLogger.logError("SCREEN_CAPTURE", "Bitmap.wrapHardwareBuffer = NULL", null)
                                        callback(null)
                                    }
                                } catch (e: Exception) {
                                    StructuredLogger.logError("SCREEN_CAPTURE", "Ошибка конвертации HardwareBuffer", e)
                                    callback(null)
                                } finally {
                                    hwBuffer.close()
                                }
                            }

                            override fun onFailure(errorCode: Int) {
                                StructuredLogger.logError("SCREEN_CAPTURE", "Сбой takeScreenshot(): код " + errorCode, null)
                                callback(null)
                            }
                        }
                    )
                } catch (e: Exception) {
                    StructuredLogger.logError("SCREEN_CAPTURE", "Исключение при вызове takeScreenshot()", e)
                    callback(null)
                }
            } else {
                StructuredLogger.logError("SCREEN_CAPTURE", "Android API " + Build.VERSION.SDK_INT + " < 30.", null)
                callback(null)
            }
        }, delay)
    }

    fun captureScreenBitmap(): Bitmap? {
        var result: Bitmap? = null
        val latch = CountDownLatch(1)
        captureScreenBitmapAsync { bmp ->
            result = bmp
            latch.countDown()
        }
        try {
            val success = latch.await(3000, TimeUnit.MILLISECONDS)
            if (!success) {
                StructuredLogger.logError("SCREEN_CAPTURE", "Таймаут CountDownLatch (>3000ms) при ожидании скриншота!", null)
            }
        } catch (e: Exception) {
            StructuredLogger.logError("SCREEN_CAPTURE", "Прерывание ожидания CountDownLatch", e)
        }
        return result
    }

    fun showControlPanel() {
        if (::overlayManager.isInitialized) overlayManager.showControlPanel()
    }

    fun hideControlPanel() {
        if (::overlayManager.isInitialized) overlayManager.hideControlPanel()
    }

    fun showFloatingStopButton() {
        if (::overlayManager.isInitialized) overlayManager.showFloatingStopButton()
    }

    fun hideFloatingStopButton() {
        if (::overlayManager.isInitialized) overlayManager.hideFloatingStopButton()
    }

    fun showClickVisualizer(x: Float, y: Float) {
        if (::overlayManager.isInitialized) overlayManager.showClickVisualizer(x, y)
    }
}
'''

# -----------------------------------------------------------------------------
# 3. APPLYING PATCHES WITH TRUNCATE GUARD
# -----------------------------------------------------------------------------

def apply_patch():
    print("[🚀] Starting AutoTap Property Restoration Patch (v54)...")
    patched_count = 0
    
    for rel_path, new_content in FILES_TO_PATCH.items():
        abs_path = os.path.abspath(rel_path)
        dir_path = os.path.dirname(abs_path)
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        print(f"[*] Patching file: {rel_path}...")
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.truncate(0)
            f.write(new_content)
        
        patched_count += 1

    print(f"\n[🎉] SUCCESS: Successfully restored globalPreScreenshotDelayMs property in {patched_count} files!")

if __name__ == '__main__':
    apply_patch()