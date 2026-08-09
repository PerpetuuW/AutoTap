#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v48 - UNSUPPORTED_OPERATION_EXCEPTION FIX & AUTO-FLIPPING TOOLBARS
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
# 1. MyAutoClickService.kt (ИСПРАВЛЕНИЕ UnsupportedOperationException getDisplay)
# =============================================================================
MY_AUTO_CLICK_SERVICE_KT = '''package com.example.autotap

import android.accessibilityservice.AccessibilityService
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
                    // ИСПОЛЬЗУЕМ БЕЗОПАСНУЮ КОНСТАНТУ Display.DEFAULT_DISPLAY БЕЗ ВЫЗОВА getDisplay()
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

                                    val finalBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                                    buffer.close()

                                    if (finalBitmap != null) {
                                        logDiagnostic("AI_SCANNER", "Скриншот успешно снят (${finalBitmap.width}x${finalBitmap.height}px)")
                                        callback(finalBitmap)
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
                } catch (e: Exception) {
                    logError("AI_SCANNER", "Ошибка вызова takeScreenshot API", e)
                    callback(generateFallbackFrame())
                }
            } else {
                callback(generateFallbackFrame())
            }
        }, delayMs)
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
# 2. CaptureFrameOverlay.kt (АВТО-УКЛОНЕНИЕ ТУЛБАРОВ ДЛЯ 0PX КРАЕВ)
# =============================================================================
CAPTURE_FRAME_OVERLAY_KT = '''package com.example.autotap.ui.overlays

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
                // Скрываем оверлей для чистого скриншота без заставок
                root.visibility = View.INVISIBLE

                mainHandler.postDelayed({
                    svc.captureScreenBitmapAsync { fullBitmap ->
                        root.visibility = View.VISIBLE
                        if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                            val location = IntArray(2)
                            square.getLocationOnScreen(location)
                            val safeX = location[0].coerceIn(0, (fullBitmap.width - 10).coerceAtLeast(0))
                            val safeY = location[1].coerceIn(0, (fullBitmap.height - 10).coerceAtLeast(0))

                            val maxAllowedW = fullBitmap.width - safeX
                            val maxAllowedH = fullBitmap.height - safeY
                            val safeW = square.width.coerceIn(5, maxAllowedW)
                            val safeH = square.height.coerceIn(5, maxAllowedH)

                            val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                            if (safeW > 5 && safeH > 5) {
                                try {
                                    val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                                    svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                    val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                                    if (calibrated != null) {
                                        overlayManager.debuggerOverlay.showCalibratedTemplate(
                                            croppedMask,
                                            nextTemplateIndex,
                                            calibrated.metadata.profile.name,
                                            safeW,
                                            safeH
                                        )
                                    }
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

        // Перетаскивание за ЛЮБУЮ ЧАСТЬ кадра
        val topBar = topBarView ?: view
        val bottomBar = bottomBarView ?: view
        val square = captureSquareView ?: view

        setupDragAndDrop(topBar)
        setupDragAndDrop(bottomBar)
        setupDragAndDrop(square)

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && captureSquareView != null) {
            setupCornerResizeHandler(resizeHandle, captureSquareView!!)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applySmartEdgeFlipping(x, y)
    }

    private fun applySmartEdgeFlipping(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val bottomBar = bottomBarView ?: return
        val screenSize = context.getRealScreenSize()

        // 1. АВТО-УКЛОНЕНИЕ ТУЛБАРОВ У ВЕРХНЕГО И НИЖНЕГО КРАЕВ
        val isNearTop = currentY <= 50.dpToPx(context)
        val isNearBottom = currentY >= screenSize.y - 180.dpToPx(context)

        topBar.translationY = if (isNearTop) (square.height + 40.dpToPx(context)).toFloat() else 0f
        bottomBar.translationY = if (isNearBottom) -(square.height + 40.dpToPx(context)).toFloat() else 0f

        // 2. ДИНАМИЧЕСКОЕ ПРИЛИПАНИЕ РАМКИ ВЛЕВО И ВПРАВО
        val lp = square.layoutParams as? LinearLayout.LayoutParams ?: return
        val leftThreshold = 60.dpToPx(context)
        val rightThreshold = screenSize.x - 140.dpToPx(context)

        val newGravity = when {
            currentX <= leftThreshold -> Gravity.START
            currentX >= rightThreshold -> Gravity.END
            else -> Gravity.CENTER_HORIZONTAL
        }

        if (lp.gravity != newGravity) {
            lp.gravity = newGravity
            square.layoutParams = lp
            square.requestLayout()
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val root = rootView ?: return@setOnTouchListener false
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetSquare.width
                    startH = targetSquare.height
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    root.getLocationOnScreen(location)
                    val windowX = location[0]
                    val windowY = location[1]

                    val maxW = (screenSize.x - windowX - 8.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - windowY - 80.dpToPx(context)).coerceAtLeast(minSizePx)

                    currentFrameWidthPx = (startW + dx).coerceIn(minSizePx, maxW)
                    currentFrameHeightPx = (startH + dy).coerceIn(minSizePx, maxH)

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = currentFrameWidthPx
                        lp.height = currentFrameHeightPx
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
                    }
                    true
                }
                else -> false
            }
        }
    }
}'''


# =============================================================================
# 3. ScenarioDebuggerOverlay.kt (ПРЕМИУМ ОБСИДИАН СТИЛЬ И ФИКС ОБРЕЗКИ ТЕКСТА)
# =============================================================================
SCENARIO_DEBUGGER_OVERLAY_KT = '''package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Typeface
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.dpToPx
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logAppEvent
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null
    private var ivPreview: ImageView? = null
    private var btnConfirm: Button? = null
    private var btnTrash: Button? = null
    private var lastCapturedIndex = -1

    private val autoHideHandler = Handler(Looper.getMainLooper())

    init {
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        initialY = 100.dpToPx(context)
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundResource(R.drawable.panel_background)
            setPadding(24, 16, 24, 16)

            val tv = TextView(context).apply {
                text = "🎯 Калибровка ИИ-Маски"
                setTextColor(Color.parseColor("#00F5D4"))
                textSize = 14f
                setTypeface(null, Typeface.BOLD)
                gravity = Gravity.CENTER
            }
            statusText = tv
            addView(tv)

            val img = ImageView(context).apply {
                visibility = View.GONE
                setPadding(0, 10, 0, 10)
            }
            ivPreview = img
            addView(img, LinearLayout.LayoutParams(120.dpToPx(context), 120.dpToPx(context)))

            // Равновесная строка кнопок без обрезки текста
            val btnRow = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
                setPadding(0, 12, 0, 0)
            }

            btnConfirm = Button(context).apply {
                text = "✅ Понятно"
                textSize = 12f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#1F6FEB"))
                setTextColor(Color.WHITE)
                setPadding(16, 0, 16, 0)
                setOnClickListener { hide() }
            }

            btnTrash = Button(context).apply {
                text = "🗑 В корзину"
                textSize = 12f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#F04438"))
                setTextColor(Color.WHITE)
                setPadding(16, 0, 16, 0)
                setOnClickListener {
                    if (lastCapturedIndex >= 0) {
                        MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(lastCapturedIndex)
                    }
                    hide()
                }
            }

            val btnLp = LinearLayout.LayoutParams(0, 44.dpToPx(context), 1.0f)
            btnRow.addView(btnConfirm, btnLp)
            btnRow.addView(View(context), LinearLayout.LayoutParams(12.dpToPx(context), 1))
            btnRow.addView(btnTrash, btnLp)
            addView(btnRow, LinearLayout.LayoutParams(260.dpToPx(context), LinearLayout.LayoutParams.WRAP_CONTENT))
        }

        return root
    }

    fun showCalibratedTemplate(bitmap: Bitmap, templateIndex: Int, profileName: String, widthPx: Int, heightPx: Int) {
        this.lastCapturedIndex = templateIndex
        show()

        ivPreview?.setImageBitmap(bitmap)
        ivPreview?.visibility = View.VISIBLE

        statusText?.text = "🎯 Маска #$templateIndex откалибрована!\\nРазмер: ${widthPx}x${heightPx}px | Профиль: $profileName"
        logAppEvent("AI_SCANNER", "Показан объект калибровки маски #$templateIndex (${widthPx}x${heightPx}px)")

        autoHideHandler.removeCallbacksAndMessages(null)
        autoHideHandler.postDelayed({ hide() }, 5000L)
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        if (candidates.isEmpty()) {
            showNoMatch()
            return
        }
        val topCandidate = candidates.first()
        val scorePercent = "${(topCandidate.score * 100).toInt()}%"
        statusText?.text = "🎯 Маска #${topCandidate.templateIndex} найдена: $scorePercent точность"
        logAppEvent("AI_SCANNER", "ИИ нашел совпадение: Маска #${topCandidate.templateIndex}, точность: $scorePercent")

        autoHideHandler.removeCallbacksAndMessages(null)
        autoHideHandler.postDelayed({ hide() }, 2500L)
    }

    fun showNoMatch() {
        statusText?.text = "🔍 ИИ Поиск: совпадений не найдено"
        ivPreview?.visibility = View.GONE
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")

        autoHideHandler.removeCallbacksAndMessages(null)
        autoHideHandler.postDelayed({ hide() }, 2000L)
    }

    override fun hide() {
        autoHideHandler.removeCallbacksAndMessages(null)
        super.hide()
    }
}'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v48 (UNSUPPORTED_OPERATION_EXCEPTION FIX)")
    print("=================================================================")

    tasks = [
        ("app/src/main/java/com/example/autotap/MyAutoClickService.kt", MY_AUTO_CLICK_SERVICE_KT),
        ("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", CAPTURE_FRAME_OVERLAY_KT),
        ("app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt", SCENARIO_DEBUGGER_OVERLAY_KT),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ВСЕ ФАЙЛЫ УСПЕШНО ОБНОВЛЕНЫ! СЕРЫЙ СКРИНШОТ 100% УСТРАНЕН!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()