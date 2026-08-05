
package com.example.autotap.ui.overlays
import com.example.autotap.*

import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.PointF
import android.graphics.drawable.GradientDrawable
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.ui.base.OverlayManager

class CandidateSelectionOverlay(
    private val service: MyAutoClickService,
    private val overlayManager: OverlayManager
) {

    private var rootView: FrameLayout? = null
    private val candidates = mutableListOf<View>()

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
            isClickable = true

            setOnTouchListener { _, event ->
                if (event.action == MotionEvent.ACTION_DOWN) {
                    handleTap(PointF(event.rawX, event.rawY))
                }
                true
            }
        }

        overlayManager.safeAddView(rootView, params)
    }

    fun hide() {
        clearCandidates()
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }

    fun clearCandidates() {
        candidates.forEach { c ->
            (c.parent as? ViewGroup)?.removeView(c)
        }
        candidates.clear()
    }

    fun showCandidate(point: PointF, radiusDp: Float = 20f) {
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
                setColor(0x33FFCC00)
                setStroke(overlayManager.dpToPx(2f), Color.YELLOW)
            }

            alpha = 1f
        }

        container.addView(circle)
        candidates.add(circle)

        circle.animate()
            .alpha(0.0f)
            .setDuration(600L)
            .withEndAction {
                (circle.parent as? ViewGroup)?.removeView(circle)
                candidates.remove(circle)
            }
            .start()
    }

    private fun handleTap(point: PointF) {
        service.onCandidateSelected(point)
    }
}
