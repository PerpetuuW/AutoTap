package com.example.autotap.engine

import android.view.View
import android.widget.ImageButton
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import java.util.concurrent.CountDownLatch

class ScriptExecutor(private val service: MyAutoClickService) {

    private var executionThread: Thread? = null

    fun startExecutionLoop() {
        if (executionThread != null) return
        executionThread = Thread {
            var currentIndex = 0
            service.uiExecutor.execute {
                service.controlPanelView?.visibility = View.GONE
                service.joystickOverlay.hide()
                service.showFloatingStopButton()
            }
            while (service.isPlaying && service.actionsList.isNotEmpty()) {
                val action = service.actionsList[currentIndex]

                try { Thread.sleep(action.delay) } catch (e: InterruptedException) { break }
                if (!service.isPlaying) break

                when (action.type) {
                    ActionType.CLICK -> {
                        var clickX = 0f; var clickY = 0f
                        val latch = CountDownLatch(1)
                        service.uiExecutor.execute {
                            val loc = IntArray(2)
                            action.startView.getLocationOnScreen(loc)
                            val size = if (action.startView.width > 0) action.startView.width else service.overlayManager.dpToPx(36)
                            clickX = loc[0] + size / 2f
                            clickY = loc[1] + size / 2f
                            latch.countDown()
                        }
                        try { latch.await() } catch (_: Exception) {}
                        service.showClickVisualizer(clickX, clickY)
                        service.gestureExecutor.performClickWithCallback(clickX, clickY, service.globalClickDurationMs)
                    }
                    ActionType.SWIPE -> {
                        if (action.endView != null) {
                            var startX = 0f; var startY = 0f; var endX = 0f; var endY = 0f
                            val latch = CountDownLatch(1)
                            service.uiExecutor.execute {
                                val loc1 = IntArray(2); action.startView.getLocationOnScreen(loc1)
                                val loc2 = IntArray(2); action.endView!!.getLocationOnScreen(loc2)
                                val size = if (action.startView.width > 0) action.startView.width else service.overlayManager.dpToPx(36)
                                startX = loc1[0] + size / 2f; startY = loc1[1] + size / 2f
                                endX = loc2[0] + size / 2f; endY = loc2[1] + size / 2f
                                latch.countDown()
                            }
                            try { latch.await() } catch (_: Exception) {}
                            if (action.joystickPath.isNotEmpty()) {
                                service.gestureExecutor.performPathSwipeWithCallback(
                                    action.joystickPath, startX, startY, endX, endY, action.holdDuration
                                )
                            } else {
                                service.gestureExecutor.performSwipeWithCallback(
                                    startX, startY, endX, endY, action.holdDuration
                                )
                            }
                        }
                    }
                    ActionType.TRIGGER -> {
                        val jumpTargetStepId = service.aiScannerEngine.executeAiTriggerSequence(action)
                        if (jumpTargetStepId == -999) {
                            currentIndex = 0
                            continue
                        } else if (jumpTargetStepId > 0) {
                            val targetIdx = service.actionsList.indexOfFirst { it.id == jumpTargetStepId }
                            if (targetIdx != -1) {
                                currentIndex = targetIdx
                                continue
                            }
                        }
                    }
                    ActionType.JOYSTICK_PATH -> {
                    if (action.joystickPath.isNotEmpty()) {
                        val first = action.joystickPath.first()
                        val last = action.joystickPath.last()
                        service.gestureExecutor.performPathSwipeWithCallback(
                            action.joystickPath,
                            first.x, first.y,
                            last.x, last.y,
                            action.holdDuration
                        )
                    }
                }
                ActionType.JOYSTICK_PATH -> {
                    if action.joystickPath:
                        first = action.joystickPath[0]
                        last = action.joystickPath[-1]
                        service.gestureExecutor.performPathSwipeWithCallback(
                            action.joystickPath,
                            first.x, first.y,
                            last.x, last.y,
                            action.holdDuration
                        )
                }
                else -> {}
                }

                val nextIdx = (currentIndex + 1) % service.actionsList.size
                currentIndex = nextIdx
            }
            service.isPlaying = false
            service.uiExecutor.execute {
                service.stopExecutionLoop()
            }
        }
        executionThread?.start()
    }

    fun stopExecutionLoop() {
        service.isPlaying = false
        executionThread?.interrupt()
        executionThread = null
        service.uiExecutor.execute {
            service.hideFloatingStopButton()
            service.controlPanelView?.visibility = View.VISIBLE
            val playBtn = service.controlPanelView?.findViewById<ImageButton>(R.id.btnPlay)
            playBtn?.setImageResource(R.drawable.ic_play)
            service.setTargetsTouchable(true)
        }
    }
}
