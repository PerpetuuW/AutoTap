package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import kotlin.math.max

class SearchAreaOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val minSizePx = 32.dpToPx(context)
    private var currentWidthPx = 200.dpToPx(context)
    private var currentHeightPx = 200.dpToPx(context)

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = currentWidthPx
        height = currentHeightPx
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_search_area_frame, null)

        view.bindClickByNames("btnSaveSearchArea") {
            logDiagnostic("AI_SCANNER", "Область поиска сохранена: ${currentWidthPx}x${currentHeightPx}px")
            hide()
        }

        view.bindClickByNames("btnResetSearchArea", "btnCancelSearchArea") {
            hide()
        }

        val handle = view.findViewByNames("handleMoveSearchArea", "layoutSearchTopBar") ?: view
        setupDragAndDrop(handle)

        val resizeHandle = view.findViewByNames("handleResizeSearchArea")
        if (resizeHandle != null) {
            setupResizeHandler(resizeHandle)
        }

        return view
    }

    private fun setupResizeHandler(resizeView: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = lp.width.takeIf { it > 0 } ?: currentWidthPx
                    startH = lp.height.takeIf { it > 0 } ?: currentHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    currentWidthPx = max(minSizePx, startW + dx)
                    currentHeightPx = max(minSizePx, startH + dy)

                    lp.width = currentWidthPx
                    lp.height = currentHeightPx
                    width = currentWidthPx
                    height = currentHeightPx

                    try {
                        windowManager.updateViewLayout(overlayView, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка ресайза области поиска", e)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
