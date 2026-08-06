package com.example.autotap.engine

import android.graphics.PointF
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType

class ScriptExecutor(private val service: MyAutoClickService) {

    @Volatile private var isRunning = false
    @Volatile var currentStepIndex = 0
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
        service.hideControlPanel()
        service.showFloatingStopButton()

        logDiagnostic("SCRIPT", "Запуск сценария (${service.actionsList.size} шагов).")
        executeNextStep()
    }

    fun stop() {
        isRunning = false
        service.isPlaying = false
        currentStepIndex = 0
        service.hideFloatingStopButton()
        service.showControlPanel()
        logDiagnostic("SCRIPT", "Сценарий остановлен.")
    }

    fun jumpToStep(stepIndex: Int) {
        if (stepIndex in 0 until service.actionsList.size) {
            currentStepIndex = stepIndex
            logDiagnostic("SCRIPT", "Переход на шаг $stepIndex")
            executeNextStep()
        } else {
            logError("SCRIPT", "Недопустимый шаг для перехода: $stepIndex", null)
            stop()
        }
    }

    private fun executeNextStep() {
        if (!isRunning) return
        val actions = service.actionsList
        if (currentStepIndex >= actions.size) {
            logDiagnostic("SCRIPT", "Сценарий успешно завершен.")
            stop()
            return
        }

        val action = actions[currentStepIndex]
        logDiagnostic("SCRIPT", "Выполнение шага $currentStepIndex: тип=${action.type.name}")

        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)

        when (action.type) {
            ActionType.CLICK -> {
                service.showClickVisualizer(pt.x, pt.y)
                service.gestureExecutor.performClickWithJitter(pt.x, pt.y, action.randomRadius, action.holdDuration) { success ->
                    onStepCompleted(success, action)
                }
            }
            ActionType.LONG_PRESS -> {
                service.showClickVisualizer(pt.x, pt.y)
                service.gestureExecutor.performLongPress(pt.x, pt.y, action.holdDuration) { success ->
                    onStepCompleted(success, action)
                }
            }
            ActionType.SWIPE -> {
                val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                service.gestureExecutor.performSwipe(pt.x, pt.y, endPt.x, endPt.y, action.holdDuration) { success ->
                    onStepCompleted(success, action)
                }
            }
            ActionType.JOYSTICK_PATH -> {
                if (action.joystickPath.isNotEmpty()) {
                    logDiagnostic("SCRIPT", "Воспроизведение записанной траектории джойстика (${action.joystickPath.size} точек)")
                    service.gestureExecutor.performJoystickPath(action.joystickPath, action.holdDuration) { success ->
                        onStepCompleted(success, action)
                    }
                } else {
                    onStepCompleted(false, action)
                }
            }
            ActionType.AI_SEARCH -> {
                logDiagnostic("SCRIPT", "Запуск AI поиска для шага $currentStepIndex")
                service.aiScannerEngine.scanAsync({ service.captureScreenBitmap() }, action) { foundPoint ->
                    if (foundPoint != null) {
                        service.showClickVisualizer(foundPoint.x, foundPoint.y)
                        service.gestureExecutor.performClick(foundPoint.x, foundPoint.y, service.globalClickDurationMs) { success ->
                            onStepCompleted(success, action)
                        }
                    } else {
                        onStepCompleted(false, action)
                    }
                }
            }
            ActionType.WAIT -> {
                Thread.sleep(action.delay.coerceAtLeast(10L))
                onStepCompleted(true, action)
            }
            ActionType.LOAD_SCRIPT -> {
                val targetName = action.targetScriptToLoad
                if (targetName != null && targetName.isNotEmpty()) {
                    val loaded = service.loadScriptByName(targetName)
                    if (loaded) {
                        currentStepIndex = 0
                        executeNextStep()
                        return
                    }
                }
                onStepCompleted(false, action)
            }
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
        if (action.delay > 0) {
            Thread.sleep(action.delay)
        }
        executeNextStep()
    }
}
