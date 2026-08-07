package com.example.autotap.engine

import android.graphics.PointF
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CopyOnWriteArrayList

class RecordingEngine(private val service: MyAutoClickService) {

    @Volatile var isRecording = false
        private set

    @Volatile var isJoystickRecording = false
        private set

    val recordedActions = CopyOnWriteArrayList<ActionConfig>()
    val joystickRecordedPath = CopyOnWriteArrayList<PointF>()

    fun startRecording() {
        if (isRecording) return
        isRecording = true
        recordedActions.clear()
        logDiagnostic("RECORDING", "Начата системная запись сценария.")
    }

    fun stopRecording(scriptName: String? = null): Boolean {
        if (!isRecording) return false
        isRecording = false

        val finalName = if (!scriptName.isNullOrEmpty()) {
            scriptName
        } else {
            "script_${SimpleDateFormat("MMdd_HHmm", Locale.US).format(Date())}"
        }

        logDiagnostic("RECORDING", "Запись остановлена. Сохранение '$finalName' (${recordedActions.size} шагов).")

        if (recordedActions.isNotEmpty()) {
            service.actionsList.clear()
            service.actionsList.addAll(recordedActions)
            service.saveScriptByName(finalName, ArrayList(recordedActions))
            return true
        }
        return false
    }

    fun startJoystickRecording() {
        isJoystickRecording = true
        joystickRecordedPath.clear()
        logDiagnostic("RECORDING", "Начата обособленная запись траектории джойстика.")
    }

    fun finishJoystickRecording(action: ActionConfig, customName: String? = null) {
        if (action.joystickPath.isNotEmpty()) {
            isJoystickRecording = false
            recordedActions.add(action)
            service.actionsList.add(action)
            val name = customName ?: "joystick_${SimpleDateFormat("MMdd_HHmm", Locale.US).format(Date())}"
            service.saveScriptByName(name, ArrayList(service.actionsList))
            logDiagnostic("RECORDING", "Завершена отдельная запись джойстика '$name' (${action.joystickPath.size} точек).")
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
}
