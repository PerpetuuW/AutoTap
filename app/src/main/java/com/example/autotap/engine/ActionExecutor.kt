package com.example.autotap.engine

import android.os.Build
import android.util.Log
import kotlinx.coroutines.*
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import com.example.autotap.*

class ActionExecutor(
    private val scenarioManager: ScenarioManager
) {
    private var executionJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private val aiScannerEngine = AiScannerEngine()

    @Volatile
    var isRunning: Boolean = false
        private set

    fun startExecution() {
        if (isRunning) return
        isRunning = true
        logStructured("Execution engine STARTED")

        executionJob = scope.launch {
            while (isActive && isRunning) {
                val actions = scenarioManager.getActions()
                if (actions.isEmpty()) {
                    delay(500L)
                    continue
                }

                for (action in actions) {
                    if (!isActive || !isRunning) break
                    val startTime = System.currentTimeMillis()

                    executeSingleAction(action)

                    val elapsed = System.currentTimeMillis() - startTime
                    logStructured("Executed action #${action.index} (${action.type}) in ${elapsed}ms. Delaying ${action.delayAfterMs}ms")
                    delay(action.delayAfterMs.coerceAtLeast(10L))
                }
            }
        }
    }

    fun stopExecution() {
        isRunning = false
        executionJob?.cancel()
        executionJob = null
        logStructured("Execution engine STOPPED")
    }

    private suspend fun executeSingleAction(action: AutoTapAction) {
        val service = AutoTapAccessibilityService.instance
        if (service == null) {
            logStructured("ERROR: AutoTapAccessibilityService instance is NULL")
            return
        }

        when (action.type) {
            ActionType.CLICK -> {
                service.performClick(action.x.toFloat(), action.y.toFloat(), action.durationMs)
            }
            ActionType.SWIPE -> {
                service.performSwipe(
                    action.x.toFloat(), action.y.toFloat(),
                    action.endX.toFloat(), action.endY.toFloat(),
                    action.durationMs
                )
            }
            ActionType.DELAY -> {
                delay(action.durationMs)
            }
            ActionType.AI_COLOR_SCAN -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    val matchPoint = aiScannerEngine.scanWithStabilization(action)
                    if (matchPoint != null) {
                        service.performClick(matchPoint.x.toFloat(), matchPoint.y.toFloat(), action.durationMs)
                    }
                } else {
                    logStructured("AI_COLOR_SCAN requires Android 11 (API 30)+")
                }
            }
        }
    }

    private fun logStructured(msg: String) {
        val time = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        Log.d("ActionExecutor", "[$time] $msg")
    }
}
