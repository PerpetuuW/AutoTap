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

    fun setFocusable(focusable: Boolean) {
        val lp = layoutParams ?: params ?: return
        val view = overlayView ?: rootView ?: return
        if (focusable) {
            lp.flags = lp.flags and WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE.inv()
        } else {
            lp.flags = lp.flags or WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        }
        try {
            windowManager.updateViewLayout(view, lp)
        } catch (_: Exception) {}
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
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) отображен.")
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
        val v = overlayView ?: rootView
        
        if (v != null && (v.width == 0 || v.height == 0)) {
            v.measure(
                View.MeasureSpec.makeMeasureSpec(screenSize.x, View.MeasureSpec.AT_MOST),
                View.MeasureSpec.makeMeasureSpec(screenSize.y, View.MeasureSpec.AT_MOST)
            )
        }

        val viewW = v?.measuredWidth?.takeIf { it > 0 } ?: v?.width?.takeIf { it > 0 } ?: width.takeIf { it > 0 } ?: 140
        val viewH = v?.measuredHeight?.takeIf { it > 0 } ?: v?.height?.takeIf { it > 0 } ?: height.takeIf { it > 0 } ?: 140

        val maxX = (screenSize.x - viewW).coerceAtLeast(0)
        val maxY = (screenSize.y - viewH).coerceAtLeast(0)
        lp.x = lp.x.coerceIn(0, maxX)
        lp.y = lp.y.coerceIn(0, maxY)
    }

    open fun updatePosition(x: Int, y: Int) {
        val lp = layoutParams ?: params ?: return
        if (width != WindowManager.LayoutParams.MATCH_PARENT) {
            val screenSize = context.getRealScreenSize()
            val v = overlayView ?: rootView
            val viewW = v?.width?.takeIf { it > 0 } ?: width.takeIf { it > 0 } ?: 140
            val viewH = v?.height?.takeIf { it > 0 } ?: height.takeIf { it > 0 } ?: 140

            val maxX = (screenSize.x - viewW).coerceAtLeast(0)
            val maxY = (screenSize.y - viewH).coerceAtLeast(0)

            lp.x = x.coerceIn(0, maxX)
            lp.y = y.coerceIn(0, maxY)
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
        val v = overlayView ?: rootView
        val w = v?.width?.takeIf { it > 0 } ?: if (width > 0) width else 200
        val h = v?.height?.takeIf { it > 0 } ?: if (height > 0) height else 200
        return Rect(lp.x, lp.y, lp.x + w, lp.y + h)
    }

    protected fun setupDragAndDrop(handleView: View) {
        var startX = 0f
        var startY = 0f
        var isDragging = false

        handleView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = event.rawX
                    startY = event.rawY
                    isDragging = false
                    true // ВОЗВРАЩАЕМ TRUE, ЧТОБЫ ОС ПЕРЕДАВАЛА ACTION_MOVE
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - startX).toInt()
                    val dy = (event.rawY - startY).toInt()

                    if (!isDragging && (abs(dx) > touchSlop || abs(dy) > touchSlop)) {
                        isDragging = true
                    }

                    if (isDragging) {
                        updatePosition(lp.x + dx, lp.y + dy)
                        startX = event.rawX
                        startY = event.rawY
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    val wasDragging = isDragging
                    isDragging = false
                    true
                }
                else -> false
            }
        }
    }
}
