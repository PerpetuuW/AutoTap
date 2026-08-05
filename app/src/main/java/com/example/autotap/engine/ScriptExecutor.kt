package com.example.autotap.engine

import com.example.autotap.*

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
                        val jitter = service.randomOffset(action.randomRadius)
                        val fx = pt.first + jitter.x
                        val fy = pt.second + jitter.y

                        uiHandler.post {
                            service.showClickVisualizer(fx, fy)
                            service.debuggerOverlay.update(action)
                        }

                        service.gestureExecutor.performClickWithCallback(fx, fy, service.globalClickDurationMs)
                    }

                    ActionType.LONG_PRESS, ActionType.HOLD -> {
                        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        uiHandler.post {
                            service.showClickVisualizer(pt.first, pt.second)
                            service.debuggerOverlay.update(action)
                        }
                        service.gestureExecutor.performClickWithCallback(pt.first, pt.second, action.holdDuration)
                    }

                    ActionType.SWIPE -> {
                        val startPt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                        uiHandler.post { service.debuggerOverlay.update(action) }

                        if (action.joystickPath.isNotEmpty()) {
                            val path = action.joystickPath.map { p ->
                                val normP = service.resolveNormalizedPoint(p.x, p.y)
                                PointF(normP.first, normP.second)
                            }
                            service.gestureExecutor.performPathSwipeWithCallback(path, startPt.first, startPt.second, endPt.first, endPt.second, action.holdDuration)
                        } else {
                            service.gestureExecutor.performSwipeWithCallback(startPt.first, startPt.second, endPt.first, endPt.second, action.holdDuration)
                        }
                    }

                    ActionType.SWIPE_PATH -> {
                        val startPt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                        val path = action.joystickPath.map { p ->
                            val normP = service.resolveNormalizedPoint(p.x, p.y)
                            PointF(normP.first, normP.second)
                        }
                        service.gestureExecutor.performPathSwipeWithCallback(path, startPt.first, startPt.second, endPt.first, endPt.second, action.holdDuration)
                    }

                    ActionType.WAIT -> {
                        when (action.waitType) {
                            "TIME" -> Thread.sleep(action.delay)
                            "TEMPLATE_APPEAR" -> {
                                val start = System.currentTimeMillis()
                                while (service.isPlaying && (System.currentTimeMillis() - start < action.holdDuration)) {
                                    val match = service.aiScannerEngine.scanForMatch(service.captureScreenBitmap(), action)
                                    if (match != null) break
                                    Thread.sleep(100)
                                }
                            }
                            "TEMPLATE_DISAPPEAR" -> {
                                val start = System.currentTimeMillis()
                                while (service.isPlaying && (System.currentTimeMillis() - start < action.holdDuration)) {
                                    val match = service.aiScannerEngine.scanForMatch(service.captureScreenBitmap(), action)
                                    if (match == null) break
                                    Thread.sleep(100)
                                }
                            }
                        }
                    }

                    ActionType.LOOP -> {
                        if (action.loopCount > 1) {
                            action.loopCount--
                            currentIndex = action.loopStartIndex.coerceIn(0, service.actionsList.size - 1)
                            continue
                        }
                    }

                    ActionType.TRIGGER -> {
                        uiHandler.post { service.debuggerOverlay.update(action) }
                        val scanResult = service.aiScannerEngine.executeAiTriggerSequence(action)

                        when {
                            scanResult.targetScript.isNotEmpty() -> {
                                service.loadScriptByName(scanResult.targetScript)
                                currentIndex = 0
                                continue
                            }
                            scanResult.jumpToStep > 0 -> {
                                val targetIdx = service.actionsList.indexOfFirst { it.id == scanResult.jumpToStep }
                                if (targetIdx != -1) {
                                    currentIndex = targetIdx
                                    continue
                                }
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
