package com.example.autotap.ui.overlays

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PointF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.FrameLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.dpToPx
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.vibrateFeedback
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

class JoystickOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val joystickPath = mutableListOf<PointF>()
    private var isKnobActive = false

    init {
        width = 240.dpToPx(context)
        height = 240.dpToPx(context)
        gravity = Gravity.BOTTOM or Gravity.START
        initialX = 50
        initialY = 100
        layer = OverlayLayer.JOYSTICK_LAYER
    }

    override fun createView(): View {
        val root = FrameLayout(context).apply {
            setBackgroundColor(Color.TRANSPARENT)
        }

        val joystickView = ActiveJoystickView(context) { event, cx, cy, distanceRatio ->
            handleActiveKnobTouch(event, cx, cy, distanceRatio)
        }

        root.addView(joystickView, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ))

        setupDragAndDrop(root)
        return root
    }

    private fun handleActiveKnobTouch(event: MotionEvent, cx: Float, cy: Float, distanceRatio: Float) {
        val lp = layoutParams ?: return
        val service = MyAutoClickService.instance ?: return
        val globalPoint = PointF(lp.x + width / 2f + cx, lp.y + height / 2f + cy)

        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                isKnobActive = true
                joystickPath.clear()
                service.recordingEngine.startJoystickRecording()
                logDiagnostic("JOYSTICK", "Активный режим Knob: запуск управления и записи.")
            }
            MotionEvent.ACTION_MOVE -> {
                if (!isKnobActive) return

                // 1. Логирование траектории
                joystickPath.add(globalPoint)

                // 2. Вызов реального жеста в игре (Активный режим)
                if (distanceRatio > 0.05f) {
                    val centerX = lp.x + width / 2f
                    val centerY = lp.y + height / 2f
                    service.gestureExecutor.performJoystickRealtime(cx, cy, centerX, centerY)
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (isKnobActive) {
                    isKnobActive = false
                    logDiagnostic("JOYSTICK", "Knob отпущен. Сохранение записанной траектории (${joystickPath.size} точек).")

                    val action = ActionConfig(
                        type = ActionType.JOYSTICK_PATH,
                        joystickPath = joystickPath.toList(),
                        holdDuration = (joystickPath.size * 25L).coerceAtLeast(200L)
                    )
                    service.recordingEngine.finishJoystickRecording(action)
                    context.vibrateFeedback()
                }
            }
        }
    }

    private class ActiveJoystickView(
        context: Context,
        private val onKnobMove: (event: MotionEvent, cx: Float, cy: Float, ratio: Float) -> Unit
    ) : View(context) {

        private val basePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#66333333")
            style = Paint.Style.FILL
        }

        private val baseStrokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#AABBBBBB")
            style = Paint.Style.STROKE
            strokeWidth = 6f
        }

        private val knobPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#DD00E676")
            style = Paint.Style.FILL
        }

        private var centerX = 0f
        private var centerY = 0f
        private var baseRadius = 0f
        private var knobRadius = 0f

        private var knobX = 0f
        private var knobY = 0f

        override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
            super.onSizeChanged(w, h, oldw, oldh)
            centerX = w / 2f
            centerY = h / 2f
            baseRadius = (w.coerceAtMost(h) / 2f) * 0.8f
            knobRadius = baseRadius * 0.35f
            knobX = centerX
            knobY = centerY
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            canvas.drawCircle(centerX, centerY, baseRadius, basePaint)
            canvas.drawCircle(centerX, centerY, baseRadius, baseStrokePaint)
            canvas.drawCircle(knobX, knobY, knobRadius, knobPaint)
        }

        @SuppressLint("ClickableViewAccessibility")
        override fun onTouchEvent(event: MotionEvent): Boolean {
            val dx = event.x - centerX
            val dy = event.y - centerY
            val distance = sqrt(dx * dx + dy * dy)

            when (event.action) {
                MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                    val clampedDx: Float
                    val clampedDy: Float

                    if (distance < baseRadius) {
                        knobX = event.x
                        knobY = event.y
                        clampedDx = dx
                        clampedDy = dy
                    } else {
                        val angle = atan2(dy, dx)
                        clampedDx = cos(angle) * baseRadius
                        clampedDy = sin(angle) * baseRadius
                        knobX = centerX + clampedDx
                        knobY = centerY + clampedDy
                    }
                    val ratio = (distance / baseRadius).coerceIn(0f, 1f)
                    invalidate()
                    onKnobMove(event, clampedDx, clampedDy, ratio)
                    return true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    // Анимация возврата Knob в центр
                    knobX = centerX
                    knobY = centerY
                    invalidate()
                    onKnobMove(event, 0f, 0f, 0f)
                    return true
                }
            }
            return super.onTouchEvent(event)
        }
    }
}
