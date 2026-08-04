package com.example.autotap.ui.debug

import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.PointF
import android.graphics.RectF
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ScenarioDebuggerOverlay(private val service: MyAutoClickService) {

    private var overlayView: DebugView? = null

    fun show() {
        if (overlayView != null) return

        overlayView = DebugView(service)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }

        service.overlayManager.safeAddView(overlayView, params)
    }

    fun hide() {
        overlayView?.let { service.overlayManager.safeRemoveView(it) }
        overlayView = null
    }

    fun update(config: ActionConfig) {
        overlayView?.update(config)
    }

    // ---------------------------------------------------------
    // Внутренний класс — кастомный Canvas‑View
    // ---------------------------------------------------------
    private class DebugView(context: MyAutoClickService) : View(context) {

        private var cfg: ActionConfig? = null
        private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            strokeWidth = 3f
            style = Paint.Style.STROKE
        }

        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 32f
        }

        fun update(config: ActionConfig) {
            cfg = config
            invalidate()
        }

        override fun onDraw(canvas: android.graphics.Canvas) {
            super.onDraw(canvas)
            val c = cfg ?: return

            // ---------------------------------------------------------
            // ТЕКСТ: номер шага + тип
            // ---------------------------------------------------------
            canvas.drawText(
                "STEP ${c.id} — ${c.type}",
                20f,
                50f,
                textPaint
            )

            // ---------------------------------------------------------
            // CLICK / LONG_PRESS визуализация
            // ---------------------------------------------------------
            if (c.type == ActionType.CLICK || c.type == ActionType.LONG_PRESS) {
                val (x, y) = (context as MyAutoClickService).resolveNormalizedPoint(c.xNorm, c.yNorm)

                paint.color = Color.GREEN
                canvas.drawCircle(x, y, 40f, paint)

                canvas.drawText("Click @ ($x,$y)", x + 50, y, textPaint)
            }

            // ---------------------------------------------------------
            // SWIPE визуализация
            // ---------------------------------------------------------
            if (c.type == ActionType.SWIPE) {
                val svc = context as MyAutoClickService
                val (sx, sy) = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                val (ex, ey) = svc.resolveNormalizedPoint(c.endXNorm, c.endYNorm)

                paint.color = Color.CYAN
                canvas.drawCircle(sx, sy, 30f, paint)
                canvas.drawCircle(ex, ey, 30f, paint)
                canvas.drawLine(sx, sy, ex, ey, paint)

                canvas.drawText("Swipe", sx + 50, sy, textPaint)

                // джойстик‑траектория
                if (c.joystickPath.isNotEmpty()) {
                    paint.color = Color.MAGENTA
                    val path = Path()
                    val svc2 = context as MyAutoClickService

                    val first = c.joystickPath.first()
                    val (fx, fy) = svc2.resolveNormalizedPoint(first.x, first.y)
                    path.moveTo(fx, fy)

                    for (p in c.joystickPath.drop(1)) {
                        val (px, py) = svc2.resolveNormalizedPoint(p.x, p.y)
                        path.lineTo(px, py)
                    }

                    canvas.drawPath(path, paint)
                    canvas.drawText("Joystick path", fx + 50, fy, textPaint)
                }
            }

            // ---------------------------------------------------------
            // TRIGGER визуализация
            // ---------------------------------------------------------
            if (c.type == ActionType.TRIGGER) {
                val svc = context as MyAutoClickService

                // область поиска
                if (c.customSearchArea) {
                    val (sx, sy) = svc.resolveNormalizedPoint(c.searchAreaXNorm, c.searchAreaYNorm)
                    val (ex, ey) = svc.resolveNormalizedPoint(
                        c.searchAreaXNorm + c.searchAreaWNorm,
                        c.searchAreaYNorm + c.searchAreaHNorm
                    )

                    paint.color = Color.YELLOW
                    canvas.drawRect(RectF(sx, sy, ex, ey), paint)
                    canvas.drawText("Search area", sx + 20, sy + 40, textPaint)
                }

                // калибровка
                c.calibratedRectNorm?.let { r ->
                    val (sx, sy) = svc.resolveNormalizedPoint(r.left.toFloat(), r.top.toFloat())
                    val (ex, ey) = svc.resolveNormalizedPoint(r.right.toFloat(), r.bottom.toFloat())

                    paint.color = Color.RED
                    canvas.drawRect(RectF(sx, sy, ex, ey), paint)
                    canvas.drawText("Calibrated", sx + 20, sy + 40, textPaint)
                }

                canvas.drawText("Trigger mode", 20f, 100f, textPaint)
            }
        }
    }
}
