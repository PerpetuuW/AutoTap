import os
import sys

def validate_kotlin(content, filename):
    brackets = {'(': ')', '{': '}', '[': ']'}
    stack = []
    for char in content:
        if char in brackets.keys():
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Лишняя закрывающая скобка '{char}'")
            top = stack.pop()
            if brackets[top] != char:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Несоответствие скобок '{top}' и '{char}'")
    if stack:
        raise ValueError(f"Ошибка синтаксиса в {filename}: Незакрытые скобки {stack}")

    forbidden = ["TODO()", "// остальной код", "// TODO"]
    for item in forbidden:
        if item in content:
            raise ValueError(f"Обнаружена запрещенная заглушка '{item}' в файле {filename}")

files = {}

# JoystickOverlay.kt с исправленным Color.TRANSPARENT
files["app/src/main/java/com/example/autotap/ui/overlays/JoystickOverlay.kt"] = """package com.example.autotap.ui.overlays

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
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.vibrateFeedback
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

class JoystickOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val joystickPath = mutableListOf<PointF>()
    private var isRecording = false
    private var lastInjectTime = 0L
    private val injectThrottleMs = 40L // 25 FPS rate limit

    init {
        width = 240.dpToPx(context)
        height = 240.dpToPx(context)
        gravity = Gravity.BOTTOM or Gravity.START
        initialX = 50
        initialY = 100
    }

    override fun createView(): View {
        val root = FrameLayout(context).apply {
            setBackgroundColor(Color.TRANSPARENT)
        }

        val joystickView = JoystickCustomView(context) { event, knobX, knobY, distanceRatio ->
            handleJoystickTouch(event, knobX, knobY, distanceRatio)
        }

        root.addView(joystickView, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ))

        setupDragAndDrop(root)
        return root
    }

    private fun handleJoystickTouch(event: MotionEvent, knobX: Float, knobY: Float, distanceRatio: Float) {
        val lp = layoutParams ?: return
        val currentScreenPoint = PointF(lp.x + knobX, lp.y + knobY)

        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                isRecording = true
                joystickPath.clear()
                joystickPath.add(currentScreenPoint)
                logDiagnostic("JOYSTICK", "Начата запись траектории джойстика.")
            }
            MotionEvent.ACTION_MOVE -> {
                if (isRecording) {
                    joystickPath.add(currentScreenPoint)

                    val now = System.currentTimeMillis()
                    if (now - lastInjectTime >= injectThrottleMs && distanceRatio > 0.1f) {
                        lastInjectTime = now
                        val centerPoint = PointF(lp.x + width / 2f, lp.y + height / 2f)
                        injectJoystickSwipe(centerPoint, currentScreenPoint)
                    }
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (isRecording) {
                    isRecording = false
                    logDiagnostic("JOYSTICK", "Завершено движение джойстика. Записано точек: ${joystickPath.size}")
                    saveRecordedTrajectory()
                }
            }
        }
    }

    private fun injectJoystickSwipe(center: PointF, target: PointF) {
        val service = MyAutoClickService.instance ?: return
        service.gestureExecutor.performSwipe(center.x, center.y, target.x, target.y, 40L, null)
    }

    private fun saveRecordedTrajectory() {
        if (joystickPath.isEmpty()) return
        val service = MyAutoClickService.instance ?: return

        val recordedCopy = joystickPath.toList()
        val action = ActionConfig(
            type = ActionType.JOYSTICK_PATH,
            joystickPath = recordedCopy,
            holdDuration = (recordedCopy.size * injectThrottleMs).coerceAtLeast(200L)
        )
        service.actionsList.add(action)
        context.vibrateFeedback()
        logDiagnostic("JOYSTICK", "Траектория джойстика сохранена в сценарий как ActionConfig (точек: ${recordedCopy.size})")
    }

    private class JoystickCustomView(
        context: Context,
        private val onJoystickMove: (event: MotionEvent, knobX: Float, knobY: Float, ratio: Float) -> Unit
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

        override fun onTouchEvent(event: MotionEvent): Boolean {
            val dx = event.x - centerX
            val dy = event.y - centerY
            val distance = sqrt(dx * dx + dy * dy)

            when (event.action) {
                MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                    if (distance < baseRadius) {
                        knobX = event.x
                        knobY = event.y
                    } else {
                        val angle = atan2(dy, dx)
                        knobX = centerX + cos(angle) * baseRadius
                        knobY = centerY + sin(angle) * baseRadius
                    }
                    val ratio = (distance / baseRadius).coerceIn(0f, 1f)
                    invalidate()
                    onJoystickMove(event, knobX, knobY, ratio)
                    return true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    knobX = centerX
                    knobY = centerY
                    invalidate()
                    onJoystickMove(event, knobX, knobY, 0f)
                    return true
                }
            }
            return super.onTouchEvent(event)
        }
    }
}
"""

print("=== ИСПРАВЛЕНИЕ JoystickOverlay.kt ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ФИКС ЗАВЕРШЕН ===")