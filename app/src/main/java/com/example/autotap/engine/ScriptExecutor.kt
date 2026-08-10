package com.example.autotap.engine

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
}
