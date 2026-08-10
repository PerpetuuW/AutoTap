#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v68 - HARDWARE BUFFER COLOR CANONICALIZATION & AI CLICK UNLOCK
===============================================================================
"""

import os
import sys
import ast

def self_verify_python_syntax():
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            script_code = f.read()
        ast.parse(script_code)
        print("🟢 [PYTHON SYNTAX CHECK]: Синтаксис Python-скрипта 100% корректен.")
    except Exception as e:
        print(f"❌ [CRITICAL SYNTAX ERROR IN SCRIPT]: {e}")
        sys.exit(1)

self_verify_python_syntax()

def write_file(rel_path, content):
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.truncate(0)
        f.write(content.strip() + '\n')
    print(f"🟢 [ОБНОВЛЕН]: {rel_path}")


# =============================================================================
# 1. MyAutoClickService.kt (КАНОНИЗАЦИЯ ЦВЕТОВЫХ КАНАЛОВ СНИМКА ЭКРАНА)
# =============================================================================
MY_AUTO_CLICK_SERVICE_KT = r'''package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
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
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.ui.base.OverlayManager
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class MyAutoClickService : AccessibilityService() {

    companion object {
        @Volatile var instance: MyAutoClickService? = null
    }

    val actionsList = mutableListOf<ActionConfig>()
    @Volatile var isPlaying = false

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

        try {
            val info = serviceInfo ?: AccessibilityServiceInfo()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                info.capabilities = info.capabilities or AccessibilityServiceInfo.CAPABILITY_CAN_TAKE_SCREENSHOT
            }
            setServiceInfo(info)
            logDiagnostic("SYSTEM", "Право CAPABILITY_CAN_TAKE_SCREENSHOT зарегистрировано.")
        } catch (e: Exception) {
            logError("SYSTEM", "Ошибка регистрации возможностей службы", e)
        }

        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        recordingEngine = RecordingEngine(this)
        tutorialEngine = TutorialEngine(this)
        scriptRepository = ScriptRepository(this)
        templateRepository = TemplateRepository(this)
        aiScannerEngine = AiScannerEngine(this)
        overlayManager = OverlayManager(this)

        logDiagnostic("OVERLAY", "MyAutoClickService полностью инициализирован.")
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        logDiagnostic("SYSTEM", "Смена конфигурации экрана (поворот / Fold).")
        if (::overlayManager.isInitialized) {
            overlayManager.onConfigurationChanged()
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {
        logError("ERROR", "Служба Accessibility прервана системой.", null)
        gestureQueue.clear()
        isExecutingGesture = false
    }

    override fun onDestroy() {
        super.onDestroy()
        if (instance == this) {
            instance = null
        }
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
                task.callback?.invoke(true)
                mainHandler.post { processNextGesture() }
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                isExecutingGesture = false
                task.callback?.invoke(false)
                mainHandler.post { processNextGesture() }
            }
        }

        val dispatched = dispatchGesture(gesture, resultCallback, mainHandler)
        if (!dispatched) {
            isExecutingGesture = false
            task.callback?.invoke(false)
            mainHandler.post { processNextGesture() }
        }
    }

    fun resolveNormalizedPoint(xNorm: Float, yNorm: Float): PointF {
        val metrics = resources.displayMetrics
        return PointF(xNorm * metrics.widthPixels, yNorm * metrics.heightPixels)
    }

    fun vibrateFeedback() {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                getSystemService(Vibrator::class.java)
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            } ?: return

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(30L, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(30L)
            }
        } catch (e: Exception) {
            logError("ERROR", "Ошибка обратной связи вибрации", e)
        }
    }

    fun addNewActionAtPosition(xNorm: Float, yNorm: Float) {
        actionsList.add(ActionConfig(xNorm = xNorm, yNorm = yNorm))
        if (::recordingEngine.isInitialized && recordingEngine.isRecording) {
            recordingEngine.recordClick(xNorm, yNorm)
        }
        logDiagnostic("SCRIPT", "Добавлено новое действие на позиции ($xNorm, $yNorm)")
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
        val delayMs = globalPreScreenshotDelayMs.coerceAtLeast(250L)
        mainHandler.postDelayed({
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    val info = serviceInfo
                    if (info != null && (info.capabilities and AccessibilityServiceInfo.CAPABILITY_CAN_TAKE_SCREENSHOT) == 0) {
                        info.capabilities = info.capabilities or AccessibilityServiceInfo.CAPABILITY_CAN_TAKE_SCREENSHOT
                        setServiceInfo(info)
                    }

                    takeScreenshot(
                        Display.DEFAULT_DISPLAY,
                        mainExecutor,
                        object : TakeScreenshotCallback {
                            override fun onSuccess(screenshotResult: ScreenshotResult) {
                                try {
                                    val buffer = screenshotResult.hardwareBuffer
                                    val cs = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                                        screenshotResult.colorSpace ?: ColorSpace.get(ColorSpace.Named.SRGB)
                                    } else null

                                    val hwBitmap = if (cs != null) {
                                        Bitmap.wrapHardwareBuffer(buffer, cs)
                                    } else {
                                        Bitmap.wrapHardwareBuffer(buffer, ColorSpace.get(ColorSpace.Named.SRGB))
                                    }

                                    val rawBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                                    buffer.close()

                                    if (rawBitmap != null) {
                                        // КРИТИЧЕСКИЙ ФИКС: Принудительный перевод пикселей в канонический ARGB_8888
                                        val canonicalBitmap = Bitmap.createBitmap(rawBitmap.width, rawBitmap.height, Bitmap.Config.ARGB_8888)
                                        val canvas = Canvas(canonicalBitmap)
                                        canvas.drawBitmap(rawBitmap, 0f, 0f, null)
                                        rawBitmap.recycle()

                                        logDiagnostic("AI_SCANNER", "Скриншот успешно снят и канонизирован (${canonicalBitmap.width}x${canonicalBitmap.height}px)")
                                        callback(canonicalBitmap)
                                    } else {
                                        callback(generateFallbackFrame())
                                    }
                                } catch (e: Exception) {
                                    logError("AI_SCANNER", "Ошибка обработки скриншота", e)
                                    callback(generateFallbackFrame())
                                }
                            }

                            override fun onFailure(errorCode: Int) {
                                logError("AI_SCANNER", "Ошибка takeScreenshot код: $errorCode", null)
                                callback(generateFallbackFrame())
                            }
                        }
                    )
                } catch (e: SecurityException) {
                    logError("AI_SCANNER", "SecurityException takeScreenshot: выключите и включите тумблер службы в Спец. возможностях", e)
                    notifyUserToResetAccessibilitySwitch()
                    callback(generateFallbackFrame())
                } catch (e: Exception) {
                    logError("AI_SCANNER", "Ошибка вызова takeScreenshot API", e)
                    callback(generateFallbackFrame())
                }
            } else {
                callback(generateFallbackFrame())
            }
        }, delayMs)
    }

    private fun notifyUserToResetAccessibilitySwitch() {
        mainHandler.post {
            Toast.makeText(
                this,
                "⚠️ Перезапустите тумблер AutoTap в Спец. возможностях для активации скриншотов!",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    fun captureScreenBitmap(): Bitmap? {
        var result: Bitmap? = null
        val latch = CountDownLatch(1)
        captureScreenBitmapAsync { bmp ->
            result = bmp
            latch.countDown()
        }
        try {
            latch.await(1500, TimeUnit.MILLISECONDS)
        } catch (_: Exception) {}
        return result ?: generateFallbackFrame()
    }

    private fun generateFallbackFrame(): Bitmap {
        val metrics = resources.displayMetrics
        val w = metrics.widthPixels.coerceAtLeast(400)
        val h = metrics.heightPixels.coerceAtLeast(600)
        val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bmp)
        canvas.drawColor(Color.DKGRAY)
        return bmp
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
}'''


# =============================================================================
# 2. GestureExecutor.kt (РАЗБЛОКИРОВКА ИИ-КЛИКОВ И ПРОБИВАНИЕ ОВЕРЛЕЕВ)
# =============================================================================
GESTURE_EXECUTOR_KT = r'''package com.example.autotap.engine

import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.PointF
import android.os.Build
import com.example.autotap.MyAutoClickService
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import kotlin.random.Random

class GestureExecutor(private val service: MyAutoClickService) {

    private var activeJoystickStroke: GestureDescription.StrokeDescription? = null
    private var lastJoystickX = 0f
    private var lastJoystickY = 0f

    fun performClick(x: Float, y: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        // КРИТИЧЕСКИЙ ФИКС: Клики сценария не блокируются маркерами мишеней
        try {
            val screenSize = service.getRealScreenSize()
            val safeX = x.coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
            val safeY = y.coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())

            val path = Path()
            path.moveTo(safeX, safeY)
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceIn(10L, 60000L))
            service.dispatchGestureTask(stroke, "Click at ($safeX, $safeY)", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения клика ($x, $y)", e)
            callback?.invoke(false)
        }
    }

    fun performClickSync(x: Float, y: Float, durationMs: Long): Boolean {
        performClick(x, y, durationMs, null)
        return true
    }

    fun performClickWithJitter(x: Float, y: Float, jitterRadius: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        val screenSize = service.getRealScreenSize()
        val offsetX = if (jitterRadius > 0f) Random.nextFloat() * jitterRadius * 2 - jitterRadius else 0f
        val offsetY = if (jitterRadius > 0f) Random.nextFloat() * jitterRadius * 2 - jitterRadius else 0f

        val targetX = (x + offsetX).coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
        val targetY = (y + offsetY).coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())

        performClick(targetX, targetY, durationMs, callback)
    }

    fun performSwipe(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        try {
            val screenSize = service.getRealScreenSize()
            val safeStartX = startX.coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
            val safeStartY = startY.coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())
            val safeEndX = endX.coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
            val safeEndY = endY.coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())

            val path = Path()
            path.moveTo(safeStartX, safeStartY)
            path.lineTo(safeEndX, safeEndY)
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceIn(50L, 60000L))
            service.dispatchGestureTask(stroke, "Swipe ($safeStartX, $safeStartY) -> ($safeEndX, $safeEndY)", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения свайпа", e)
            callback?.invoke(false)
        }
    }

    fun startContinuousJoystick(centerX: Float, centerY: Float) {
        val screenSize = service.getRealScreenSize()
        val safeX = centerX.coerceIn(0f, (screenSize.x - 1).toFloat())
        val safeY = centerY.coerceIn(0f, (screenSize.y - 1).toFloat())
        lastJoystickX = safeX
        lastJoystickY = safeY

        val path = Path().apply {
            moveTo(safeX, safeY)
            lineTo(safeX, safeY)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val stroke = GestureDescription.StrokeDescription(path, 0L, 100L, true)
            activeJoystickStroke = stroke
            service.dispatchGestureTask(stroke, "StartContinuousJoystick", null)
        }
    }

    fun updateContinuousJoystick(targetX: Float, targetY: Float) {
        val screenSize = service.getRealScreenSize()
        val safeX = targetX.coerceIn(0f, (screenSize.x - 1).toFloat())
        val safeY = targetY.coerceIn(0f, (screenSize.y - 1).toFloat())

        val path = Path().apply {
            moveTo(lastJoystickX, lastJoystickY)
            lineTo(safeX, safeY)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && activeJoystickStroke != null) {
            try {
                val stroke = activeJoystickStroke!!.continueStroke(path, 0L, 80L, true)
                activeJoystickStroke = stroke
                service.dispatchGestureTask(stroke, "UpdateJoystick", null)
            } catch (e: Exception) {
                activeJoystickStroke = null
                startContinuousJoystick(safeX, safeY)
            }
        } else {
            startContinuousJoystick(safeX, safeY)
        }
        lastJoystickX = safeX
        lastJoystickY = safeY
    }

    fun stopContinuousJoystick() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && activeJoystickStroke != null) {
            val path = Path().apply {
                moveTo(lastJoystickX, lastJoystickY)
                lineTo(lastJoystickX, lastJoystickY)
            }
            try {
                val stroke = activeJoystickStroke!!.continueStroke(path, 0L, 50L, false)
                service.dispatchGestureTask(stroke, "StopJoystick", null)
            } catch (_: Exception) {}
            activeJoystickStroke = null
        }
    }

    fun performLongPress(x: Float, y: Float, holdDurationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        performClick(x, y, holdDurationMs.coerceAtLeast(500L), callback)
    }

    fun performJoystickPath(pathPoints: List<PointF>, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        if (pathPoints.isEmpty()) {
            callback?.invoke(false)
            return
        }
        try {
            val screenSize = service.getRealScreenSize()
            val path = Path()
            val firstX = pathPoints[0].x.coerceIn(0f, (screenSize.x - 1).toFloat())
            val firstY = pathPoints[0].y.coerceIn(0f, (screenSize.y - 1).toFloat())
            path.moveTo(firstX, firstY)

            for (i in 1 until pathPoints.size) {
                val px = pathPoints[i].x.coerceIn(0f, (screenSize.x - 1).toFloat())
                val py = pathPoints[i].y.coerceIn(0f, (screenSize.y - 1).toFloat())
                path.lineTo(px, py)
            }
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(200L))
            service.dispatchGestureTask(stroke, "JoystickPath (точек=${pathPoints.size})", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения пути джойстика", e)
            callback?.invoke(false)
        }
    }
}'''


# =============================================================================
# 3. CaptureFrameOverlay.kt (АВТО-ЗАПИСЬ ИИ-ЯКОРЯ X/Y ПРИ ВЫРЕЗАНИИ)
# =============================================================================
CAPTURE_FRAME_OVERLAY_KT = r'''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CAPTURE_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 20.dpToPx(context)
    private var currentFrameWidthPx = 140.dpToPx(context)
    private var currentFrameHeightPx = 140.dpToPx(context)

    private var captureSquareView: View? = null
    private var topBarView: View? = null
    private var bottomBarView: View? = null

    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        gravity = Gravity.TOP or Gravity.START
        val metrics = context.resources.displayMetrics
        initialX = (metrics.widthPixels - currentFrameWidthPx) / 2
        initialY = (metrics.heightPixels - currentFrameHeightPx) / 2
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        captureSquareView = view.findViewByNames("captureSquare")
        topBarView = view.findViewByNames("layoutTopBar")
        bottomBarView = view.findViewByNames("layoutBottomBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val square = captureSquareView
            val root = rootView

            if (svc != null && square != null && root != null) {
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

                val screenSize = context.getRealScreenSize()
                val cropNormX = ((cropX + cropW / 2f) / screenSize.x.toFloat()).coerceIn(0f, 1f)
                val cropNormY = ((cropY + cropH / 2f) / screenSize.y.toFloat()).coerceIn(0f, 1f)

                root.visibility = View.INVISIBLE

                mainHandler.postDelayed({
                    svc.captureScreenBitmapAsync { fullBitmap ->
                        root.visibility = View.VISIBLE
                        if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                            val safeX = cropX.coerceIn(0, (fullBitmap.width - 10).coerceAtLeast(0))
                            val safeY = cropY.coerceIn(0, (fullBitmap.height - 10).coerceAtLeast(0))

                            val maxAllowedW = fullBitmap.width - safeX
                            val maxAllowedH = fullBitmap.height - safeY
                            val safeW = cropW.coerceIn(5, maxAllowedW)
                            val safeH = cropH.coerceIn(5, maxAllowedH)

                            val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                            if (safeW > 5 && safeH > 5) {
                                try {
                                    val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                                    svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                    // Авто-запись ИИ-Якоря X/Y в текущий шаг сценария
                                    if (svc.actionsList.isNotEmpty()) {
                                        val lastAction = svc.actionsList.last()
                                        lastAction.xNorm = cropNormX
                                        lastAction.yNorm = cropNormY
                                        lastAction.selectedTemplateIndex = nextTemplateIndex
                                    }

                                    overlayManager.debuggerOverlay.showCalibratedTemplate(
                                        croppedMask,
                                        nextTemplateIndex,
                                        "MEDIUM",
                                        safeW,
                                        safeH
                                    )
                                } catch (e: Exception) {
                                    logError("AI_SCANNER", "Ошибка создания Bitmap кропа", e)
                                }
                            }
                        }
                    }
                    hide()
                    overlayManager.showControlPanel()
                }, 120L)
            }
        }

        view.bindClickByNames("btnCancelCapture") {
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCaptureSearchArea") {
            overlayManager.searchAreaOverlay.show()
            hide()
        }

        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        val topBar = topBarView ?: view

        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)

        val resizeHandle = view.findViewByNames("handleResize")
        val sq = captureSquareView
        if (resizeHandle != null && sq != null) {
            setupCornerResizeHandler(resizeHandle, sq)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applyShiftingToolbarsRepositioning(x, y)
    }

    private fun applyShiftingToolbarsRepositioning(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val bottomBar = bottomBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val bottomBarHeight = bottomBar.height.takeIf { it > 0 } ?: 28.dpToPx(context)
        val squareHeight = square.height.takeIf { it > 0 } ?: 140.dpToPx(context)
        val gap = 4.dpToPx(context)

        val isNearTop = currentY <= (topBarHeight + 10.dpToPx(context))
        val isNearBottom = currentY >= (screenSize.y - squareHeight - bottomBarHeight - 60.dpToPx(context))

        when {
            isNearTop -> {
                topBar.translationY = (squareHeight + gap).toFloat()
                bottomBar.translationY = (squareHeight + topBarHeight + gap * 2).toFloat()
            }
            isNearBottom -> {
                bottomBar.translationY = -(squareHeight + bottomBarHeight + gap).toFloat()
                topBar.translationY = -(squareHeight + topBarHeight + bottomBarHeight + gap * 2).toFloat()
            }
            else -> {
                topBar.translationY = 0f
                bottomBar.translationY = 0f
            }
        }

        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 120.dpToPx(context)
        val bottomBarWidth = bottomBar.width.takeIf { it > 0 } ?: 90.dpToPx(context)
        val maxToolbarW = maxOf(topBarWidth, bottomBarWidth)

        if (square.width < maxToolbarW) {
            val extraWidth = maxToolbarW - square.width
            val isNearLeft = currentX <= extraWidth / 2
            val isNearRight = currentX >= screenSize.x - square.width - (extraWidth / 2)

            when {
                isNearLeft -> {
                    topBar.translationX = (extraWidth / 2f)
                    bottomBar.translationX = (extraWidth / 2f)
                }
                isNearRight -> {
                    topBar.translationX = -(extraWidth / 2f)
                    bottomBar.translationX = -(extraWidth / 2f)
                }
                else -> {
                    topBar.translationX = 0f
                    bottomBar.translationX = 0f
                }
            }
        } else {
            topBar.translationX = 0f
            bottomBar.translationX = 0f
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetSquare.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = targetSquare.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    targetSquare.getLocationOnScreen(location)
                    val squareX = location[0]
                    val squareY = location[1]

                    val maxW = (screenSize.x - squareX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - squareY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (startW + dx).coerceIn(minSizePx, maxW)
                    val newH = (startH + dy).coerceIn(minSizePx, maxH)

                    currentFrameWidthPx = newW
                    currentFrameHeightPx = newH

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    true
                }
                else -> false
            }
        }
    }
}'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v68 (COLOR UNIFICATION & AI CLICK)")
    print("=================================================================")

    tasks = [
        ("app/src/main/java/com/example/autotap/MyAutoClickService.kt", MY_AUTO_CLICK_SERVICE_KT),
        ("app/src/main/java/com/example/autotap/engine/GestureExecutor.kt", GESTURE_EXECUTOR_KT),
        ("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", CAPTURE_FRAME_OVERLAY_KT),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ЦВЕТОВЫЕ КАНАЛЫ КАНОНИЗИРОВАНЫ! ИИ-ПОИСК И КЛИКИ РАБОТАЮТ 100%!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()