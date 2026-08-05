package com.example.autotap.ui.overlays

import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.PointF
import android.graphics.drawable.GradientDrawable
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.ui.base.OverlayManager

class ClickVisualizerOverlay(
    private val service: MyAutoClickService,
    private val overlayManager: OverlayManager
) {

    private var rootView: FrameLayout? = null

    fun show() {
        if (rootView != null) return

        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            format = PixelFormat.TRANSLUCENT
            flags =
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        }

        rootView = FrameLayout(service).apply {
            setBackgroundColor(Color.TRANSPARENT)
            isClickable = false
        }

        overlayManager.safeAddView(rootView, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }

    fun showClick(point: PointF, radiusDp: Float = 18f, durationMs: Long = 250L) {
        val container = rootView ?: return

        val radiusPx = overlayManager.dpToPx(radiusDp)
        val circle = View(service).apply {
            layoutParams = FrameLayout.LayoutParams(
                radiusPx * 2,
                radiusPx * 2
            ).apply {
                leftMargin = (point.x - radiusPx).toInt()
                topMargin = (point.y - radiusPx).toInt()
            }

            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(0x55FFFFFF)
                setStroke(overlayManager.dpToPx(2f), Color.WHITE)
            }

            alpha = 1f
        }

        container.addView(circle)

        circle.animate()
            .alpha(0f)
            .setDuration(durationMs)
            .withEndAction {
                (circle.parent as? ViewGroup)?.removeView(circle)
            }
            .start()
    }
}
