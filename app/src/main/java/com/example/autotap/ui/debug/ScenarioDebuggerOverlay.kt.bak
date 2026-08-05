package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.*
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority

class ScenarioDebuggerOverlay(service: MyAutoClickService) :
    OverlayBase(service, 0, OverlayLayer.DEBUG, OverlayPriority.HIGH) {

    private var debugCanvasView: DebugCanvasView? = null

    override fun show() {
        if (isShowing) return
        val view = DebugCanvasView(service)
        debugCanvasView = view
        rootView = view
        val params = createParams()
        service.overlayManager.safeAddView(view, params)
        onAttach()
        fadeIn()
    }

    override fun onViewInflated(view: View) {}

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }
    }

    fun update(config: ActionConfig) {
        if (!isShowing) show()
        debugCanvasView?.updateConfig(config)
    }

    class DebugCanvasView(context: Context) : View(context) {
        private var cfg: ActionConfig? = null

        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.CYAN
            textSize = 34f
            typeface = Typeface.DEFAULT_BOLD
        }

        private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        private val heatPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            alpha = 70
        }

        fun updateConfig(config: ActionConfig) {
            cfg = config
            invalidate()
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val c = cfg ?: return
            val svc = MyAutoClickService.instance ?: return

            canvas.drawText("STEP #${c.id} [${c.type.name}] | Delay: ${c.delay}ms | Reps: ${c.repeatCount}", 40f, 100f, textPaint)

            when (c.type) {
                ActionType.CLICK, ActionType.LONG_PRESS, ActionType.HOLD -> {
                    val pt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                    strokePaint.color = Color.GREEN
                    canvas.drawCircle(pt.first, pt.second, 40f, strokePaint)
                    canvas.drawText("Target (${pt.first.toInt()}, ${pt.second.toInt()})", pt.first + 50f, pt.second, textPaint)
                }

                ActionType.SWIPE, ActionType.SWIPE_PATH -> {
                    val startPt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                    val endPt = svc.resolveNormalizedPoint(c.endXNorm, c.endYNorm)

                    strokePaint.color = Color.CYAN
                    canvas.drawCircle(startPt.first, startPt.second, 25f, strokePaint)
                    canvas.drawCircle(endPt.first, endPt.second, 25f, strokePaint)
                    canvas.drawLine(startPt.first, startPt.second, endPt.first, endPt.second, strokePaint)

                    if (c.joystickPath.isNotEmpty()) {
                        strokePaint.color = Color.MAGENTA
                        val path = Path()
                        val first = c.joystickPath.first()
                        val fPt = svc.resolveNormalizedPoint(first.x, first.y)
                        path.moveTo(fPt.first, fPt.second)

                        for (p in c.joystickPath.drop(1)) {
                            val pPt = svc.resolveNormalizedPoint(p.x, p.y)
                            path.lineTo(pPt.first, pPt.second)
                            canvas.drawCircle(pPt.first, pPt.second, 6f, strokePaint)
                        }
                        canvas.drawPath(path, strokePaint)
                    }
                }

                ActionType.TRIGGER -> {
                    if (c.customSearchArea) {
                        val startPt = svc.resolveNormalizedPoint(c.searchAreaXNorm, c.searchAreaYNorm)
                        val endPt = svc.resolveNormalizedPoint(c.searchAreaXNorm + c.searchAreaWNorm, c.searchAreaYNorm + c.searchAreaHNorm)

                        strokePaint.color = Color.YELLOW
                        val rect = RectF(startPt.first, startPt.second, endPt.first, endPt.second)
                        canvas.drawRect(rect, strokePaint)
                        canvas.drawText("Search Area (${c.similarityPercent}%)", startPt.first + 10f, startPt.second + 40f, textPaint)
                    }

                    c.calibratedRectNorm?.let { r ->
                        val startPt = svc.resolveNormalizedPoint(r.left.toFloat(), r.top.toFloat())
                        val endPt = svc.resolveNormalizedPoint(r.right.toFloat(), r.bottom.toFloat())

                        strokePaint.color = Color.RED
                        heatPaint.color = Color.RED
                        val rect = RectF(startPt.first, startPt.second, endPt.first, endPt.second)
                        canvas.drawRect(rect, heatPaint)
                        canvas.drawRect(rect, strokePaint)
                        canvas.drawText("Calibrated Mask Box", startPt.first + 10f, startPt.second + 40f, textPaint)
                    }
                }

                ActionType.WAIT -> {
                    canvas.drawText("WAIT State: ${c.waitType} (${c.holdDuration}ms)", 40f, 160f, textPaint)
                }

                ActionType.LOOP -> {
                    canvas.drawText("LOOP State: ${c.loopType} [Reps: ${c.loopCount}] -> Step #${c.loopStartIndex}", 40f, 160f, textPaint)
                }
            }
        }
    }
}
