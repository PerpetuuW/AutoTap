package com.example.autotap.ui.debug

import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.RectF
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService

class ScenarioDebuggerOverlay(private val service: MyAutoClickService) {

    private var overlayView: DebugView? = null

    fun show() {
        if (overlayView != null) return

        overlayView = DebugView(service)

        val params = service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
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
            val svc = context as MyAutoClickService

            canvas.drawText(
                "STEP ${c.id} — ${c.type}",
                20f,
                50f,
                textPaint
            )

            if (c.type == ActionType.CLICK || c.type == ActionType.LONG_PRESS) {
                val pt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                val x = pt.first
                val y = pt.second

                paint.color = Color.GREEN
                canvas.drawCircle(x, y, 40f, paint)
                canvas.drawText("Click @ ($x,$y)", x + 50, y, textPaint)
            }

            if (c.type == ActionType.SWIPE) {
                val startPt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                val endPt = svc.resolveNormalizedPoint(c.endXNorm, c.endYNorm)
                val sx = startPt.first
                val sy = startPt.second
                val ex = endPt.first
                val ey = endPt.second

                paint.color = Color.CYAN
                canvas.drawCircle(sx, sy, 30f, paint)
                canvas.drawCircle(ex, ey, 30f, paint)
                canvas.drawLine(sx, sy, ex, ey, paint)

                canvas.drawText("Swipe", sx + 50, sy, textPaint)

                if (c.joystickPath.isNotEmpty()) {
                    paint.color = Color.MAGENTA
                    val path = Path()

                    val first = c.joystickPath.first()
                    val fPt = svc.resolveNormalizedPoint(first.x, first.y)
                    path.moveTo(fPt.first, fPt.second)

                    for (p in c.joystickPath.drop(1)) {
                        val pPt = svc.resolveNormalizedPoint(p.x, p.y)
                        path.lineTo(pPt.first, pPt.second)
                    }

                    canvas.drawPath(path, paint)
                    canvas.drawText("Joystick path", fPt.first + 50, fPt.second, textPaint)
                }
            }

            if (c.type == ActionType.TRIGGER) {
                if (c.customSearchArea) {
                    val startPt = svc.resolveNormalizedPoint(c.searchAreaXNorm, c.searchAreaYNorm)
                    val endPt = svc.resolveNormalizedPoint(
                        c.searchAreaXNorm + c.searchAreaWNorm,
                        c.searchAreaYNorm + c.searchAreaHNorm
                    )
                    val sx = startPt.first
                    val sy = startPt.second
                    val ex = endPt.first
                    val ey = endPt.second

                    paint.color = Color.YELLOW
                    canvas.drawRect(RectF(sx, sy, ex, ey), paint)
                    canvas.drawText("Search area", sx + 20, sy + 40, textPaint)
                }

                c.calibratedRectNorm?.let { r ->
                    val startPt = svc.resolveNormalizedPoint(r.left.toFloat(), r.top.toFloat())
                    val endPt = svc.resolveNormalizedPoint(r.right.toFloat(), r.bottom.toFloat())
                    val sx = startPt.first
                    val sy = startPt.second
                    val ex = endPt.first
                    val ey = endPt.second

                    paint.color = Color.RED
                    canvas.drawRect(RectF(sx, sy, ex, ey), paint)
                    canvas.drawText("Calibrated", sx + 20, sy + 40, textPaint)
                }

                canvas.drawText("Trigger mode", 20f, 100f, textPaint)
            }
        }
    }
}
