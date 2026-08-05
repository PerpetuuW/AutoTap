package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.View
import android.view.WindowManager
import com.example.autotap.*

class ScenarioDebuggerOverlay(private val context: Context) {

    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var debugView: View? = null

    fun show() {
        if (debugView != null) return
        val params = windowManager.createOverlayParams()
        val view = object : View(context) {
            private val paint = Paint().apply {
                color = Color.RED
                strokeWidth = 5f
                style = Paint.Style.STROKE
            }
            override fun onDraw(canvas: Canvas) {
                super.onDraw(canvas)
                canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), paint)
            }
        }
        debugView = view
        windowManager.safeAddView(view, params)
    }

    fun update(vararg args: Any?) {
        val action = args.firstOrNull() as? AutoTapAction ?: return
        when (action.type) {
            ActionType.CLICK -> { DiagnosticLoggerLog(action) }
            ActionType.SWIPE -> { DiagnosticLoggerLog(action) }
            ActionType.COLOR_CHECK -> { DiagnosticLoggerLog(action) }
            else -> { DiagnosticLoggerLog(action) }
        }
    }

    private fun DiagnosticLoggerLog(action: AutoTapAction) {
        DiagnosticLogger.log("ScenarioDebuggerOverlay", "Debug step: ${action.id}")
    }
}
