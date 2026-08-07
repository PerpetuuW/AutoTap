package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.PointF
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import kotlin.math.sqrt

class JoystickOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var joystickBaseView: View? = null
    private var joystickKnobView: View? = null
    private var joystickContainerView: View? = null

    private var lastImpulseTime = 0L

    init {
        width = 180.dpToPx(context)
        height = 220.dpToPx(context)
        gravity = Gravity.BOTTOM or Gravity.START
        initialX = 50
        initialY = 100
        layer = OverlayLayer.JOYSTICK_LAYER
        priority = OverlayPriority.MEDIUM
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_joystick_control, null)

        joystickBaseView = view.findViewByNames("viewJoystickBase", "joystickBase")
        joystickKnobView = view.findViewByNames("viewJoystickKnob", "joystickKnob")
        joystickContainerView = view.findViewByNames("layoutJoystickContainer", "rootJoystick")

        view.bindClickByNames("btnCloseJoystick") {
            hide()
        }

        view.bindClickByNames("btnRecordJoystick") {
            logDiagnostic("JOYSTICK", "Нажата btnRecordJoystick")
            MyAutoClickService.instance?.recordingEngine?.startJoystickRecording()
        }

        setupKnobTouchListener()

        val handle = view.findViewByNames("handleMoveJoystick") ?: view
        setupDragAndDrop(handle)

        return view
    }

    private fun setupKnobTouchListener() {
        val knob = joystickKnobView ?: return
        val maxRadius = 40.dpToPx(context).toFloat()

        var startTouchX = 0f
        var startTouchY = 0f

        knob.setOnTouchListener { v, event ->
            val svc = MyAutoClickService.instance ?: return@setOnTouchListener false
            val lp = layoutParams ?: params
            val centerX = (lp?.x ?: 100) + v.width / 2f
            val centerY = (lp?.y ?: 200) + v.height / 2f

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startTouchX = event.rawX
                    startTouchY = event.rawY
                    // СТАРТ НЕПРЕРЫВНОГО ЖЕСТА В ИГРЕ
                    svc.gestureExecutor.startContinuousJoystick(centerX, centerY)
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val rawDx = event.rawX - startTouchX
                    val rawDy = event.rawY - startTouchY
                    val dist = sqrt(rawDx * rawDx + rawDy * rawDy)

                    val clampedDx = if (dist > maxRadius) (rawDx / dist) * maxRadius else rawDx
                    val clampedDy = if (dist > maxRadius) (rawDy / dist) * maxRadius else rawDy

                    knob.translationX = clampedDx
                    knob.translationY = clampedDy

                    val now = System.currentTimeMillis()
                    if (now - lastImpulseTime >= 40L) {
                        lastImpulseTime = now

                        val targetX = centerX + clampedDx
                        val targetY = centerY + clampedDy

                        // ОБНОВЛЕНИЕ НЕПРЕРЫВНОГО ЖЕСТА В ИГРЕ (willContinue = true)
                        svc.gestureExecutor.updateContinuousJoystick(targetX, targetY)

                        // ПАРАЛЛЕЛЬНАЯ ЗАПИСЬ ТРАЕКТОРИИ
                        if (svc.recordingEngine.isJoystickRecording) {
                            svc.recordingEngine.joystickRecordedPath.add(PointF(clampedDx, clampedDy))
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    knob.animate().translationX(0f).translationY(0f).setDuration(150L).start()

                    // ЗАВЕРШЕНИЕ ЖЕСТА В ИГРЕ (willContinue = false -> ACTION_UP)
                    svc.gestureExecutor.stopContinuousJoystick()

                    if (svc.recordingEngine.isJoystickRecording) {
                        val pathCopy = ArrayList(svc.recordingEngine.joystickRecordedPath)
                        val action = ActionConfig(
                            type = ActionType.JOYSTICK_PATH,
                            joystickPath = pathCopy,
                            holdDuration = (pathCopy.size * 40L).coerceAtLeast(200L)
                        )
                        svc.recordingEngine.finishJoystickRecording(action)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
