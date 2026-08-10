#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v67 - NON-BLOCKING SCREENSHOTS, OUTSIDE TOOLBARS & RUNTIME BEACON
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
# 1. CaptureFrameOverlay.kt (ФОРМУЛА СДВИГА СНАРУЖИ КАДРА БЕЗ ПЕРЕКРЫТИЯ)
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
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val squareHeight = square.height.takeIf { it > 0 } ?: 140.dpToPx(context)
        val gap = 6.dpToPx(context)

        // ТУЛБАР УХОДИТ 100% СНАРУЖИ ПОД НИЖНЮЮ ГРАНЬ КАДРА
        val isNearTop = currentY <= (topBarHeight + 10.dpToPx(context))
        topBar.translationY = if (isNearTop) (squareHeight + topBarHeight + gap * 2).toFloat() else 0f

        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 120.dpToPx(context)
        if (square.width < topBarWidth) {
            val extraWidth = topBarWidth - square.width
            val isNearLeft = currentX <= extraWidth / 2
            val isNearRight = currentX >= screenSize.x - square.width - (extraWidth / 2)

            when {
                isNearLeft -> topBar.translationX = (extraWidth / 2f)
                isNearRight -> topBar.translationX = -(extraWidth / 2f)
                else -> topBar.translationX = 0f
            }
        } else {
            topBar.translationX = 0f
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


# =============================================================================
# 2. ScriptExecutor.kt (РАНТАЙМ ОТРИСОВКА РАДАРНЫХ МАЯКОВ ПРИ ИИ-ПОИСКЕ)
# =============================================================================
SCRIPT_EXECUTOR_KT = r'''package com.example.autotap.engine

import android.os.Handler
import android.os.Looper
import com.example.autotap.MyAutoClickService
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType

class ScriptExecutor(private val service: MyAutoClickService) {

    private val mainHandler = Handler(Looper.getMainLooper())

    val gestureExecutor: GestureExecutor
        get() = service.gestureExecutor

    val aiScannerEngine: AiScannerEngine
        get() = service.aiScannerEngine

    @Volatile private var isRunning = false
    @Volatile var currentStepIndex = 0
        private set

    @Volatile var currentLoopCount = 0
        private set

    fun start() {
        if (isRunning) return
        if (service.actionsList.isEmpty()) {
            logDiagnostic("SCRIPT", "Невозможно запустить: список шагов пуст.")
            return
        }

        isRunning = true
        service.isPlaying = true
        currentStepIndex = 0
        currentLoopCount = 0
        service.hideControlPanel()
        service.showFloatingStopButton()

        logDiagnostic("SCRIPT", "Запуск сценария (${service.actionsList.size} шагов).")
        executeNextStep()
    }

    fun stop() {
        isRunning = false
        service.isPlaying = false
        currentStepIndex = 0
        currentLoopCount = 0
        mainHandler.removeCallbacksAndMessages(null)
        service.hideFloatingStopButton()
        service.showControlPanel()
        logDiagnostic("SCRIPT", "Сценарий остановлен пользователем.")
    }

    fun jumpToStep(stepIndex: Int) {
        val actions = service.actionsList
        if (stepIndex in 0 until actions.size) {
            currentStepIndex = stepIndex
            logDiagnostic("SCRIPT", "Переход на шаг $stepIndex")
            mainHandler.post { executeNextStep() }
        } else {
            logError("SCRIPT", "Недопустимый шаг для перехода: $stepIndex", null)
            stop()
        }
    }

    private fun executeNextStep() {
        if (!isRunning) return
        val actions = service.actionsList
        if (currentStepIndex >= actions.size) {
            currentLoopCount++
            logDiagnostic("SCRIPT", "Цикл сценария #$currentLoopCount выполнен.")

            val isInfinite = service.scriptRepository.currentMetadata?.isInfinite ?: true
            val maxLoops = service.scriptRepository.currentMetadata?.loopCount ?: 1

            if (isInfinite || currentLoopCount < maxLoops) {
                currentStepIndex = 0
                logDiagnostic("SCRIPT", "Повторный запуск цикла сценария (#$currentLoopCount)...")
                mainHandler.post { executeNextStep() }
                return
            } else {
                logDiagnostic("SCRIPT", "Все $maxLoops циклов сценария успешно выполнены.")
                stop()
                return
            }
        }

        val action = actions.getOrNull(currentStepIndex) ?: run {
            stop()
            return
        }

        logDiagnostic("SCRIPT", "Выполнение шага $currentStepIndex: тип=${action.type.name}")

        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)

        when (action.type) {
            ActionType.CLICK -> {
                service.showClickVisualizer(pt.x, pt.y)
                gestureExecutor.performClickWithJitter(pt.x, pt.y, action.randomRadius, action.holdDuration) { success ->
                    onStepCompleted(success, action)
                }
            }
            ActionType.LONG_PRESS -> {
                service.showClickVisualizer(pt.x, pt.y)
                gestureExecutor.performLongPress(pt.x, pt.y, action.holdDuration) { success ->
                    onStepCompleted(success, action)
                }
            }
            ActionType.SWIPE -> {
                val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                gestureExecutor.performSwipe(pt.x, pt.y, endPt.x, endPt.y, action.holdDuration) { success ->
                    onStepCompleted(success, action)
                }
            }
            ActionType.JOYSTICK_PATH -> {
                if (action.joystickPath.isNotEmpty()) {
                    gestureExecutor.performJoystickPath(action.joystickPath, action.holdDuration) { success ->
                        onStepCompleted(success, action)
                    }
                } else {
                    onStepCompleted(false, action)
                }
            }
            ActionType.AI_SEARCH -> {
                executeMultiSearchLoop(action, System.currentTimeMillis())
            }
            ActionType.WAIT -> {
                val waitDelay = action.delay.coerceAtLeast(10L)
                mainHandler.postDelayed({ onStepCompleted(true, action) }, waitDelay)
            }
            ActionType.LOAD_SCRIPT -> {
                val targetName = action.targetScriptToLoad
                if (!targetName.isNullOrEmpty()) {
                    val loaded = service.loadScriptByName(targetName)
                    if (loaded) {
                        currentStepIndex = 0
                        mainHandler.post { executeNextStep() }
                        return
                    }
                }
                onStepCompleted(false, action)
            }
        }
    }

    private fun executeMultiSearchLoop(action: ActionConfig, startTimeMs: Long) {
        if (!isRunning) return

        val timeoutMs = (action.aiTimeoutSeconds * 1000f).toLong()
        val elapsedTime = System.currentTimeMillis() - startTimeMs

        if (timeoutMs > 0L && elapsedTime >= timeoutMs) {
            logDiagnostic("AI_SCANNER", "Таймаут ИИ-поиска ($elapsedTime ms >= $timeoutMs ms) истек.")
            onStepCompleted(false, action)
            return
        }

        aiScannerEngine.scanAsync({ service.captureScreenBitmap() }, action) { foundPoint ->
            if (!isRunning) return@scanAsync

            val scanResult = aiScannerEngine.lastScanResult
            val candidates = scanResult?.candidates ?: emptyList()

            if (candidates.isNotEmpty()) {
                // Отображение неонового радарного кольца над найденными целями в рантайме!
                mainHandler.post {
                    service.overlayManager.candidateOverlay.showRadarBeaconCandidates(candidates) {
                        // Опциональный тап
                    }
                }
                clickCandidateSequence(candidates, 0, action)
            } else {
                if (action.loopUntilStopped && isRunning) {
                    val scanIntervalMs = (action.scanIntervalSeconds * 1000f).toLong().coerceAtLeast(200L)
                    mainHandler.postDelayed({ executeMultiSearchLoop(action, startTimeMs) }, scanIntervalMs)
                } else {
                    onStepCompleted(false, action)
                }
            }
        }
    }

    private fun clickCandidateSequence(candidates: List<MatchCandidate>, index: Int, action: ActionConfig) {
        if (!isRunning) return
        if (index >= candidates.size) {
            if (action.loopUntilStopped && isRunning) {
                val delayMs = action.delay.coerceAtLeast(100L)
                mainHandler.postDelayed({ executeMultiSearchLoop(action, System.currentTimeMillis()) }, delayMs)
            } else {
                onStepCompleted(true, action)
            }
            return
        }

        val candidate = candidates[index]
        val pt = candidate.point
        service.showClickVisualizer(pt.x, pt.y)

        gestureExecutor.performClick(pt.x, pt.y, service.globalClickDurationMs) { success ->
            if (!isRunning) return@performClick
            val interClickDelay = 50L
            mainHandler.postDelayed({
                clickCandidateSequence(candidates, index + 1, action)
            }, interClickDelay)
        }
    }

    private fun onStepCompleted(success: Boolean, action: ActionConfig) {
        if (!isRunning) return

        if (success) {
            val jump = action.jumpToStepOnMatch
            if (jump != null) {
                jumpToStep(jump)
                return
            }
        } else {
            val jumpFail = action.jumpToStepOnFail
            if (jumpFail != null) {
                jumpToStep(jumpFail)
                return
            }
        }

        currentStepIndex++
        val stepDelay = action.delay.coerceAtLeast(0L)
        mainHandler.postDelayed({ executeNextStep() }, stepDelay)
    }
}'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v67 (OUTSIDE TOOLBAR & RUNTIME BEACON)")
    print("=================================================================")

    tasks = [
        ("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", CAPTURE_FRAME_OVERLAY_KT),
        ("app/src/main/java/com/example/autotap/engine/ScriptExecutor.kt", SCRIPT_EXECUTOR_KT),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 СДВИГ ТУЛБАРА СНАРУЖИ И ОТРИСОВКА МАЯКОВ УСПЕШНО РЕАЛИЗОВАНЫ!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()