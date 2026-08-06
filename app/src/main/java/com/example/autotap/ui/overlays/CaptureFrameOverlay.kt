package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
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

    private val minSizePx = 24.dpToPx(context)
    private var currentFrameWidthPx = 240.dpToPx(context)
    private var currentFrameHeightPx = 240.dpToPx(context)

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = currentFrameWidthPx
        height = currentFrameHeightPx
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_capture_frame, null)

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Вырезание реальной маски с экрана (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val lp = layoutParams
            if (svc != null && lp != null) {
                val metrics = context.resources.displayMetrics
                val centerXNorm = (lp.x + currentFrameWidthPx / 2f) / metrics.widthPixels.toFloat()
                val centerYNorm = (lp.y + currentFrameHeightPx / 2f) / metrics.heightPixels.toFloat()

                svc.addNewActionAtPosition(centerXNorm.coerceIn(0f, 1f), centerYNorm.coerceIn(0f, 1f))

                val fullBitmap = svc.captureScreenBitmap()
                if (fullBitmap != null) {
                    val cropX = ((lp.x).coerceAtLeast(0)).coerceAtMost(fullBitmap.width - 20)
                    val cropY = ((lp.y).coerceAtLeast(0)).coerceAtMost(fullBitmap.height - 20)
                    val cropW = currentFrameWidthPx.coerceAtMost(fullBitmap.width - cropX)
                    val cropH = currentFrameHeightPx.coerceAtMost(fullBitmap.height - cropY)

                    if (cropW > 10 && cropH > 10) {
                        val croppedMask = Bitmap.createBitmap(fullBitmap, cropX, cropY, cropW, cropH)
                        svc.templateRepository.saveTemplate(0, croppedMask)
                        logDiagnostic("AI_SCANNER", "Реальный шаблон #0 сохранен и откалиброван (${cropW}x${cropH}px).")
                    }
                }
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

        val moveHandle = view.findViewByNames("handleMoveFrame", "layoutTopBar", "layoutCaptureContainer") ?: view
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
                    startW = lp.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = lp.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    currentFrameWidthPx = max(minSizePx, startW + dx)
                    currentFrameHeightPx = max(minSizePx, startH + dy)

                    lp.width = currentFrameWidthPx
                    lp.height = currentFrameHeightPx
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
}
