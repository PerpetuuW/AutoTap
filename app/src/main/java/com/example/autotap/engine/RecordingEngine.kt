package com.example.autotap.engine

import android.graphics.PointF
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType

class RecordingEngine(private val service: MyAutoClickService) {

    @Volatile var isRecording = false
        private set

    val recordedActions = mutableListOf<ActionConfig>()

    fun startRecording() {
        if (isRecording) return
        isRecording = true
        recordedActions.clear()
        logDiagnostic("RECORDING", "Начата запись нового сценария.")
    }

    fun stopRecording(scriptName: String = "recorded_script"): Boolean {
        if (!isRecording) return false
        isRecording = false
        logDiagnostic("RECORDING", "Запись остановлена. Всего записано действий: ${recordedActions.size}")

        if (recordedActions.isNotEmpty()) {
            service.actionsList.clear()
            service.actionsList.addAll(recordedActions)
            service.saveScriptByName(scriptName, recordedActions)
            return true
        }
        return false
    }

    fun startJoystickRecording() {
        isRecording = true
        logDiagnostic("RECORDING", "Начата активная запись джойстика.")
    }

    fun finishJoystickRecording(action: ActionConfig) {
        if (action.joystickPath.isNotEmpty()) {
            recordedActions.add(action)
            service.actionsList.add(action)
            service.saveScriptByName("recorded_joystick_script", service.actionsList)
            logDiagnostic("RECORDING", "Завершена запись джойстика (точек: ${action.joystickPath.size}).")
        }
    }

    fun recordClick(xNorm: Float, yNorm: Float, randomRadius: Float = 0f) {
        if (!isRecording) return
        val action = ActionConfig(
            type = ActionType.CLICK,
            xNorm = xNorm,
            yNorm = yNorm,
            randomRadius = randomRadius
        )
        recordedActions.add(action)
        logDiagnostic("RECORDING", "Записан клик в ($xNorm, $yNorm)")
    }

    fun recordSwipe(startXNorm: Float, startYNorm: Float, endXNorm: Float, endYNorm: Float, durationMs: Long = 300L) {
        if (!isRecording) return
        val action = ActionConfig(
            type = ActionType.SWIPE,
            xNorm = startXNorm,
            yNorm = startYNorm,
            endXNorm = endXNorm,
            endYNorm = endYNorm,
            holdDuration = durationMs
        )
        recordedActions.add(action)
        logDiagnostic("RECORDING", "Записан свайп ($startXNorm, $startYNorm) -> ($endXNorm, $endYNorm)")
    }

    fun recordAiSearch(templateIndex: Int) {
        if (!isRecording) return
        val action = ActionConfig(
            type = ActionType.AI_SEARCH,
            selectedTemplateIndex = templateIndex,
            loopUntilStopped = false
        )
        recordedActions.add(action)
        logDiagnostic("RECORDING", "Записано действие AI-поиска маски #$templateIndex")
    }
}
