package com.example.autotap.engine

import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService

class ScriptExecutor(private val service: MyAutoClickService) {

    private var executionThread: Thread? = null
    private val uiHandler = Handler(Looper.getMainLooper())

    fun startExecutionLoop() {
        if (executionThread != null) return
        if (service.actionsList.isEmpty()) return

        executionThread = Thread {
            var currentIndex = 0

            uiHandler.post {
                service.hideControlPanel()
                service.joystickOverlay.hide()
                service.showFloatingStopButton()
            }

            while (service.isPlaying && service.actionsList.isNotEmpty()) {
                val action = service.actionsList[currentIndex]

                try { Thread.sleep(action.delay) } catch (_: InterruptedException) { break }
                if (!service.isPlaying) break

                when (action.type) {
                    ActionType.CLICK -> {
                        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val x = pt.first; val y = pt.second
                        val jitter = service.randomOffset(action.randomRadius)
                        val fx = x + jitter.x; val fy = y + jitter.y

                        uiHandler.post {
                            service.showClickVisualizer(fx, fy)
                            service.debuggerOverlay.update(action)
                        }

                        service.gestureExecutor.performClickWithCallback(fx, fy, service.globalClickDurationMs)
                    }

                    ActionType.LONG_PRESS -> {
                        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val x = pt.first; val y = pt.second

                        uiHandler.post {
                            service.showClickVisualizer(x, y)
                            service.debuggerOverlay.update(action)
                        }

                        service.gestureExecutor.performClickWithCallback(x, y, action.holdDuration)
                    }

                    ActionType.SWIPE -> {
                        val startPt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                        val sx = startPt.first; val sy = startPt.second
                        val ex = endPt.first; val ey = endPt.second

                        uiHandler.post { service.debuggerOverlay.update(action) }

                        if (action.joystickPath.isNotEmpty()) {
                            val path = action.joystickPath.map { p ->
                                val normP = service.resolveNormalizedPoint(p.x, p.y)
                                PointF(normP.first, normP.second)
                            }
                            service.gestureExecutor.performPathSwipeWithCallback(path, sx, sy, ex, ey, action.holdDuration)
                        } else {
                            service.gestureExecutor.performSwipeWithCallback(sx, sy, ex, ey, action.holdDuration)
                        }
                    }

                    ActionType.TRIGGER -> {
                        uiHandler.post { service.debuggerOverlay.update(action) }
                        val jumpTargetStepId = service.aiScannerEngine.executeAiTriggerSequence(action)

                        when {
                            jumpTargetStepId == -999 -> { currentIndex = 0; continue }
                            jumpTargetStepId > 0 -> {
                                val targetIdx = service.actionsList.indexOfFirst { it.id == jumpTargetStepId }
                                if (targetIdx != -1) { currentIndex = targetIdx; continue }
                            }
                        }
                    }
                }

                currentIndex = (currentIndex + 1) % service.actionsList.size
            }

            service.isPlaying = false
            uiHandler.post { stopExecutionLoop() }
        }

        executionThread?.start()
    }

    fun stopExecutionLoop() {
        service.isPlaying = false
        executionThread?.interrupt()
        executionThread = null

        uiHandler.post {
            service.hideFloatingStopButton()
            service.showControlPanel()
            service.debuggerOverlay.hide()
        }
    }
}
