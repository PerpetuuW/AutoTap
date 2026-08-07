package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
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
    OverlayBase(context, overlayManager, OverlayLayer.CAPTURE_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 24.dpToPx(context)
    private var currentFrameWidthPx = 140.dpToPx(context)
    private var currentFrameHeightPx = 140.dpToPx(context)

    init {
        gravity = Gravity.CENTER
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        val captureSquare = view.findViewByNames("captureSquare") as? FrameLayout

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
                        
                        // АВТО-ОТКРЫТИЕ ДЕБАГ-ОВЕРЛЕЯ КАЛИБРОВКИ СРАЗУ ПОСЛЕ ВЫРЕЗАНИЯ
                        val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                        if (calibrated != null) {
                            overlayManager.debuggerOverlay.show()
                            overlayManager.debuggerOverlay.showCandidates(listOf(
                                com.example.autotap.engine.ai.MatchCandidate(
                                    point = android.graphics.PointF(safeX + safeW / 2f, safeY + safeH / 2f),
                                    score = 1.0f,
                                    boundingBox = calibrated.boundingBox,
                                    scale = 1.0f,
                                    templateIndex = nextTemplateIndex
                                )
                            ))
                        }
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

        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        setupDragAndDrop(moveHandle)

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && captureSquare != null) {
            setupResizeHandler(resizeHandle, captureSquare)
        }

        return view
    }

    private fun setupResizeHandler(resizeView: View, captureSquare: FrameLayout) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = captureSquare.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = captureSquare.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    currentFrameWidthPx = max(minSizePx, startW + dx)
                    currentFrameHeightPx = max(minSizePx, startH + dy)

                    val sqLp = captureSquare.layoutParams
                    if (sqLp != null) {
                        sqLp.width = currentFrameWidthPx
                        sqLp.height = currentFrameHeightPx
                        captureSquare.layoutParams = sqLp
                    }

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
