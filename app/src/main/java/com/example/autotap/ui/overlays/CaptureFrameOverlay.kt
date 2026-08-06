package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import com.example.autotap.MyAutoClickService
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
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    // Минимальный размер прицела снижен до 24dp для выделения микро-икон и элементов
    private val minSizePx = 24.dpToPx(context)
    private var currentWidthPx = 120.dpToPx(context)
    private var currentHeightPx = 120.dpToPx(context)

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = currentWidthPx
        height = currentHeightPx
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_capture_frame, null)

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Захват центра прицела (${currentWidthPx}x${currentHeightPx}px)")
            context.vibrateFeedback()

            val lp = layoutParams
            if (lp != null) {
                val metrics = context.resources.displayMetrics
                val centerXNorm = (lp.x + currentWidthPx / 2f) / metrics.widthPixels.toFloat()
                val centerYNorm = (lp.y + currentHeightPx / 2f) / metrics.heightPixels.toFloat()
                
                MyAutoClickService.instance?.addNewActionAtPosition(
                    centerXNorm.coerceIn(0f, 1f),
                    centerYNorm.coerceIn(0f, 1f)
                )
            }
            hide()
        }

        view.bindClickByNames("btnCancelCapture", "btn_cancel_capture", "btn_close") {
            hide()
        }

        view.bindClickByNames("btnCaptureSearchArea") {
            logDiagnostic("OVERLAY", "Переход к настройке области поиска.")
            overlayManager.searchAreaOverlay.show()
            hide()
        }

        val moveHandle = view.findViewByNames("handleMoveFrame", "layoutTopBar") ?: view
        setupDragAndDrop(moveHandle)

        val resizeHandle = view.findViewByNames("handleResize")
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
                    width = currentFrameWidthPx
                    height = currentFrameHeightPx

                    try {
                        windowManager.updateViewLayout(overlayView, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка ресайза прицела", e)
                    }
                    true
                }
                else -> false
            }
        }
    }

    private var currentFrameWidthPx: Int
        get() = currentWidthPx
        set(value) { currentWidthPx = value }

    private var currentFrameHeightPx: Int
        get() = currentHeightPx
        set(value) { currentHeightPx = value }
}
