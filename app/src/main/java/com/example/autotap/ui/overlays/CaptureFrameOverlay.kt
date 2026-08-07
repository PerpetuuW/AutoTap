package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.graphics.PointF
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
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
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

    private var currentWidthPx: Int
        get() = currentFrameWidthPx
        set(value) { currentFrameWidthPx = value }

    private var currentHeightPx: Int
        get() = currentFrameHeightPx
        set(value) { currentFrameHeightPx = value }

    private var captureSquare: FrameLayout? = null
    private var layoutTopBarView: View? = null
    private var layoutBottomBarView: View? = null

    init {
        gravity = Gravity.TOP or Gravity.START
        val metrics = context.resources.displayMetrics
        initialX = (metrics.widthPixels - currentFrameWidthPx) / 2
        initialY = (metrics.heightPixels - currentFrameHeightPx) / 2
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        captureSquare = view.findViewByNames("captureSquare") as? FrameLayout
        layoutTopBarView = view.findViewByNames("layoutTopBar")
        layoutBottomBarView = view.findViewByNames("layoutBottomBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски с экрана (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val lp = layoutParams ?: params
            if (svc != null && lp != null) {
                svc.captureScreenBitmapAsync { fullBitmap ->
                    if (fullBitmap != null && fullBitmap.width > 20 && fullBitmap.height > 20) {
                        val safeX = lp.x.coerceIn(0, (fullBitmap.width - 20).coerceAtLeast(0))
                        val safeY = lp.y.coerceIn(0, (fullBitmap.height - 20).coerceAtLeast(0))
                        val maxAllowedW = fullBitmap.width - safeX
                        val maxAllowedH = fullBitmap.height - safeY
                        val safeW = currentFrameWidthPx.coerceIn(10, maxAllowedW)
                        val safeH = currentFrameHeightPx.coerceIn(10, maxAllowedH)

                        val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                        if (safeW > 10 && safeH > 10) {
                            try {
                                val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                                svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                                if (calibrated != null) {
                                    // ОТОБРАЖЕНИЕ ОБЪЕКТА КАЛИБРОВКИ С ПРЕВЬЮ КАРТИНКИ И ПАРАМЕТРАМИ
                                    overlayManager.debuggerOverlay.showCalibratedTemplate(
                                        croppedMask,
                                        nextTemplateIndex,
                                        calibrated.metadata.profile.name,
                                        safeW,
                                        safeH
                                    )
                                }
                            } catch (e: Exception) {
                                logError("AI_SCANNER", "Ошибка создания Bitmap кропа", e)
                            }
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

        val sq = captureSquare
        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && sq != null) {
            setupResizeHandler(resizeHandle, sq)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        val lp = layoutParams ?: params ?: return
        val screenSize = context.getRealScreenSize()

        val maxX = (screenSize.x - currentFrameWidthPx).coerceAtLeast(0)
        val maxY = (screenSize.y - currentFrameHeightPx).coerceAtLeast(0)

        lp.x = x.coerceIn(0, maxX)
        lp.y = y.coerceIn(0, maxY)

        applySmartPanelFlipping(lp.x, lp.y, screenSize.x, screenSize.y)

        val v = overlayView ?: rootView ?: return
        try {
            windowManager.updateViewLayout(v, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления позиции прицела", e)
        }
    }

    private fun applySmartPanelFlipping(currentX: Int, currentY: Int, screenWidth: Int, screenHeight: Int) {
        val topBar = layoutTopBarView ?: return
        val bottomBar = layoutBottomBarView ?: return

        val topBarH = 44.dpToPx(context).toFloat()
        val bottomBarH = 44.dpToPx(context).toFloat()

        if (currentY < 120) {
            topBar.translationY = currentFrameHeightPx.toFloat() + 8f
            bottomBar.translationY = currentFrameHeightPx.toFloat() + topBarH + 16f
        } else if (currentY > screenHeight - (currentFrameHeightPx + 150)) {
            topBar.translationY = -(topBarH + bottomBarH + 16f)
            bottomBar.translationY = -bottomBarH - 8f
        } else {
            topBar.translationY = -topBarH - 8f
            bottomBar.translationY = currentFrameHeightPx.toFloat() + 8f
        }
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
                    startW = currentFrameWidthPx
                    startH = currentFrameHeightPx
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
