package com.example.autotap.ui.base

import android.content.Context
import android.graphics.Rect
import android.os.Build
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.createOverlayParams
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.safeAddView
import com.example.autotap.safeRemoveView

abstract class OverlayBase(
    protected val context: Context,
    val overlayManager: OverlayManager
) {
    protected val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    var width: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var height: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var gravity: Int = Gravity.TOP or Gravity.START
    var flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
    var dimAmount: Float = 0.5f

    var initialX: Int = 100
    var initialY: Int = 200

    var layer: OverlayLayer = OverlayLayer.PANEL_LAYER
    var priority: OverlayPriority = OverlayPriority.MEDIUM

    protected var overlayView: View? = null
    protected var layoutParams: WindowManager.LayoutParams? = null
    var isShowing: Boolean = false
        protected set

    abstract fun createView(): View

    open fun show() {
        if (isShowing) return
        try {
            val view = createView()
            view.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            overlayView = view
            val params = createOverlayParams(
                width = width,
                height = height,
                gravity = gravity,
                flags = flags,
                x = initialX,
                y = initialY
            ).apply {
                if (this@OverlayBase.dimAmount > 0f && (flags and WindowManager.LayoutParams.FLAG_DIM_BEHIND) != 0) {
                    this.dimAmount = this@OverlayBase.dimAmount
                }
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    this.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
                }
            }
            this.layoutParams = params
            val added = windowManager.safeAddView(view, params)
            if (added) {
                isShowing = true
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) отображен с поддержкой Cutout.")
            }
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка при отображении ${javaClass.simpleName}", e)
        }
    }

    open fun hide() {
        val view = overlayView ?: return
        if (isShowing) {
            try {
                windowManager.safeRemoveView(view)
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} скрыт.")
            } catch (e: Exception) {
                logError("OVERLAY", "Ошибка при скрытии ${javaClass.simpleName}", e)
            }
            overlayView = null
            isShowing = false
        }
    }

    fun setTouchable(touchable: Boolean) {
        val lp = layoutParams ?: return
        val view = overlayView ?: return
        if (touchable) {
            lp.flags = lp.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
        } else {
            lp.flags = lp.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
        }
        try {
            windowManager.updateViewLayout(view, lp)
            logDiagnostic("OVERLAY", "Флаг touchable для ${javaClass.simpleName} установлен в $touchable")
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления флага touchable", e)
        }
    }

    fun getBounds(): Rect {
        val lp = layoutParams ?: return Rect(0, 0, 0, 0)
        val w = if (width > 0) width else 200
        val h = if (height > 0) height else 200
        return Rect(lp.x, lp.y, lp.x + w, lp.y + h)
    }

    protected fun setupDragAndDrop(view: View) {
        var startX = 0
        var startY = 0
        var touchX = 0f
        var touchY = 0f

        view.setOnTouchListener { _, event ->
            val lp = layoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = lp.x
                    startY = lp.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    lp.x = startX + (event.rawX - touchX).toInt()
                    lp.y = startY + (event.rawY - touchY).toInt()
                    try {
                        windowManager.updateViewLayout(view, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка перемещения оверлея", e)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
