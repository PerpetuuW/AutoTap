package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Rect
import android.os.Build
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import androidx.core.view.ViewCompat
import com.example.autotap.createOverlayParams
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.safeAddView
import com.example.autotap.safeRemoveView
import kotlin.math.abs

abstract class OverlayBase(
    protected val context: Context,
    val overlayManager: OverlayManager,
    var layer: OverlayLayer = OverlayLayer.PANEL_LAYER,
    var priority: OverlayPriority = OverlayPriority.MEDIUM
) {
    val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    open val layoutResId: Int = 0

    var width: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var height: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var gravity: Int = Gravity.TOP or Gravity.START
    var flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
    var dimAmount: Float = 0.5f

    var initialX: Int = 100
    var initialY: Int = 200

    var overlayView: View? = null
    var rootView: View? = null
    var layoutParams: WindowManager.LayoutParams? = null
    var params: WindowManager.LayoutParams? = null
    var isShowing: Boolean = false
        protected set

    private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop

    open fun createView(): View {
        if (layoutResId != 0) {
            return LayoutInflater.from(context).inflate(layoutResId, null)
        }
        throw UnsupportedOperationException("Оверлей должен переопределить layoutResId или createView()")
    }

    open fun inflate() {
        if (rootView != null) return
        val view = createView()
        rootView = view
        overlayView = view

        val targetX = if (width == WindowManager.LayoutParams.MATCH_PARENT) 0 else initialX
        val targetY = if (height == WindowManager.LayoutParams.MATCH_PARENT) 0 else initialY

        val lp = createOverlayParams(
            width = width,
            height = height,
            gravity = gravity,
            flags = flags,
            x = targetX,
            y = targetY
        ).apply {
            if (this@OverlayBase.dimAmount > 0f && (flags and WindowManager.LayoutParams.FLAG_DIM_BEHIND) != 0) {
                this.dimAmount = this@OverlayBase.dimAmount
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                this.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        this.layoutParams = lp
        this.params = lp
        ViewCompat.setImportantForAccessibility(
            view,
            ViewCompat.IMPORTANT_FOR_ACCESSIBILITY_NO
        )
    }

    open fun show() {
        val currentView = overlayView
        if (isShowing && currentView != null) {
            try {
                windowManager.safeRemoveView(currentView)
            } catch (_: Exception) {}
            isShowing = false
        }

        try {
            inflate()
            val view = overlayView ?: rootView ?: return
            val lp = layoutParams ?: params ?: return
            reboundToScreen(lp)
            val added = windowManager.safeAddView(view, lp)
            if (added) {
                isShowing = true
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) принудительно отображен.")
            }
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка при отображении ${javaClass.simpleName}", e)
        }
    }

    open fun hide() {
        val view = overlayView ?: rootView ?: return
        if (isShowing) {
            try {
                windowManager.safeRemoveView(view)
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} скрыт.")
            } catch (e: Exception) {
                logError("OVERLAY", "Ошибка при скрытии ${javaClass.simpleName}", e)
            }
            overlayView = null
            rootView = null
            isShowing = false
        }
    }

    fun reboundToScreen(lp: WindowManager.LayoutParams) {
        if (width == WindowManager.LayoutParams.MATCH_PARENT && height == WindowManager.LayoutParams.MATCH_PARENT) {
            lp.x = 0
            lp.y = 0
            return
        }
        val screenSize = context.getRealScreenSize()
        val maxX = screenSize.x.coerceAtLeast(10)
        val maxY = screenSize.y.coerceAtLeast(10)
        lp.x = lp.x.coerceIn(-100, maxX)
        lp.y = lp.y.coerceIn(-100, maxY)
    }

    open fun updatePosition(x: Int, y: Int) {
        val lp = layoutParams ?: params ?: return
        if (width != WindowManager.LayoutParams.MATCH_PARENT) {
            val screenSize = context.getRealScreenSize()
            val viewW = overlayView?.width ?: 200
            val viewH = overlayView?.height ?: 200
            val maxX = (screenSize.x - viewW + 100).coerceAtLeast(0)
            val maxY = (screenSize.y - viewH + 100).coerceAtLeast(0)
            lp.x = x.coerceIn(-100, maxX)
            lp.y = y.coerceIn(-100, maxY)
        } else {
            lp.x = 0
            lp.y = 0
        }
        val v = overlayView ?: rootView ?: return
        try {
            windowManager.updateViewLayout(v, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления позиции $layer", e)
        }
    }

    fun setTouchable(touchable: Boolean) {
        val lp = layoutParams ?: params ?: return
        val view = overlayView ?: rootView ?: return
        if (touchable) {
            lp.flags = lp.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
        } else {
            lp.flags = lp.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
        }
        try {
            windowManager.updateViewLayout(view, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления флага touchable", e)
        }
    }

    fun getBounds(): Rect {
        val lp = layoutParams ?: params ?: return Rect(0, 0, 0, 0)
        val w = if (width > 0) width else 200
        val h = if (height > 0) height else 200
        return Rect(lp.x, lp.y, lp.x + w, lp.y + h)
    }

    protected fun setupDragAndDrop(handleView: View) {
        var lastRawX = 0f
        var lastRawY = 0f

        handleView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    lastRawX = event.rawX
                    lastRawY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - lastRawX).toInt()
                    val dy = (event.rawY - lastRawY).toInt()

                    if (dx != 0 || dy != 0) {
                        updatePosition(lp.x + dx, lp.y + dy)
                        lastRawX = event.rawX
                        lastRawY = event.rawY
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    true
                }
                else -> false
            }
        }
    }
}
