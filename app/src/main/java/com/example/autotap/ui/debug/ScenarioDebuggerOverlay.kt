package com.example.autotap.ui.debug

import android.graphics.Color
import android.graphics.Paint
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.ActionConfig
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
        if (overlayView == null) show()
        overlayView?.update(config)
    }

    private class DebugView(context: MyAutoClickService) : View(context) {

        private var cfg: ActionConfig? = null
        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.CYAN
            textSize = 36f
        }

        fun update(config: ActionConfig) {
            cfg = config
            invalidate()
        }

        override fun onDraw(canvas: android.graphics.Canvas) {
            super.onDraw(canvas)
            val c = cfg ?: return
            canvas.drawText("STEP #${c.id} [${c.type.name}]", 40f, 100f, textPaint)
        }
    }
}
