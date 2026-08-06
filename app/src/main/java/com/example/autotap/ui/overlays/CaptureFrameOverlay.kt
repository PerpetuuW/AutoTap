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
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    override val layoutResId: Int = R.layout.floating_capture_frame

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
        val view = inflater.inflate(layoutResId, null)

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски с экрана (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val lp = layoutParams ?: params
            if (svc != null && lp != null) {
                val metrics = context.resources.displayMetrics
                val centerXNorm = (lp.x + currentFrameWidthPx / 2f) / metrics.widthPixels.toFloat()
                val centerYNorm = (lp.y + currentFrameHeightPx / 2f) / metrics.heightPixels.toFloat()

                val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                val action = ActionConfig(
                    type = ActionType.AI_SEARCH,
                    xNorm = centerXNorm.coerceIn(0f, 1f),
                    yNorm = centerYNorm.coerceIn(0f, 1f),
                    selectedTemplateIndex = nextTemplateIndex
                )
                svc.actionsList.add(action)

                val fullBitmap = svc.captureScreenBitmap()
                if (fullBitmap != null && fullBitmap.width > 20 && fullBitmap.height > 20) {
                    val safeX = lp.x.coerceIn(0, (fullBitmap.width - 20).coerceAtLeast(0))
                    val safeY = lp.y.coerceIn(0, (fullBitmap.height - 20).coerceAtLeast(0))
                    val safeW = currentFrameWidthPx.coerceIn(10, fullBitmap.width - safeX)
                    val safeH = currentFrameHeightPx.coerceIn(10, fullBitmap.height - safeY)

                    if (safeW > 10 && safeH > 10) {
                        val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                        svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)
                        logDiagnostic("AI_SCANNER", "Безопасный кроп: шаблон #$nextTemplateIndex сохранен (${safeW}x${safeH}px).")
                    }
                }
            }
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCancelCapture", "btn_cancel_capture", "btn_close") {
            hide()
            overlayManager.showControlPanel()
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
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
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
                        windowManager.updateViewLayout(overlayView ?: rootView, lp)
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
