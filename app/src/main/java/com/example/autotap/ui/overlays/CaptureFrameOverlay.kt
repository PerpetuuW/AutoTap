package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.os.Handler
import android.os.Looper
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
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.abs

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CAPTURE_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 30.dpToPx(context)
    private var currentFrameWidthPx = 160.dpToPx(context)
    private var currentFrameHeightPx = 160.dpToPx(context)

    private var captureSquareView: View? = null
    private var topBarView: View? = null

    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        captureSquareView = view.findViewByNames("captureSquare")
        topBarView = view.findViewByNames("layoutTopBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture") {
            StructuredLogger.logDiagnostic("CAPTURE_FRAME", "Нажата кнопка Снятия Шаблона.")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val square = captureSquareView

            if (svc != null && square != null) {
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

                val screenSize = context.getRealScreenSize()
                val cropNormX = ((cropX + cropW / 2f) / screenSize.x.toFloat()).coerceIn(0f, 1f)
                val cropNormY = ((cropY + cropH / 2f) / screenSize.y.toFloat()).coerceIn(0f, 1f)

                overlayManager.captureCleanScreen(svc) { fullBitmap ->
                    if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                        val realMetrics = context.resources.displayMetrics
                        val scaleX = fullBitmap.width.toFloat() / realMetrics.widthPixels.toFloat()
                        val scaleY = fullBitmap.height.toFloat() / realMetrics.heightPixels.toFloat()

                        val realCropX = (cropX * scaleX).toInt().coerceIn(0, fullBitmap.width - 1)
                        val realCropY = (cropY * scaleY).toInt().coerceIn(0, fullBitmap.height - 1)
                        val realCropW = (cropW * scaleX).toInt().coerceIn(10, (fullBitmap.width - realCropX).coerceAtLeast(10))
                        val realCropH = (cropH * scaleY).toInt().coerceIn(10, (fullBitmap.height - realCropY).coerceAtLeast(10))

                        val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                        // 💥 ФИКС: Исправлена проверка размера realCropW и realCropH
                        if (realCropW > 5 && realCropH > 5) {
                            try {
                                val croppedMask = Bitmap.createBitmap(fullBitmap, realCropX, realCropY, realCropW, realCropH)
                                val saved = svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                if (saved && svc.actionsList.isNotEmpty()) {
                                    val lastAction = svc.actionsList.last()
                                    lastAction.xNorm = cropNormX
                                    lastAction.yNorm = cropNormY
                                    lastAction.selectedTemplateIndex = nextTemplateIndex
                                }

                                overlayManager.debuggerOverlay.showCalibratedTemplate(
                                    croppedMask,
                                    nextTemplateIndex,
                                    "MEDIUM",
                                    realCropW,
                                    realCropH,
                                    fullBitmap
                                )
                            } catch (e: Exception) {
                                StructuredLogger.logError("CAPTURE_FRAME", "Ошибка создания Bitmap кропа маски", e)
                            }
                        }
                    } else {
                        StructuredLogger.logError("CAPTURE_FRAME", "Скриншот вернул NULL!", null)
                    }
                }
            }
        }

        view.bindClickByNames("btnCancelCapture") {
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCaptureSearchArea") {
            overlayManager.searchAreaOverlay.show()
            hide()
        }

        val topBar = topBarView
        if (topBar != null) {
            setupIndependentViewDrag(topBar)
        }

        val frameContainer = view.findViewByNames("layoutFrameWithHandles") ?: captureSquareView
        val sq = captureSquareView

        if (frameContainer != null) {
            setupIndependentViewDrag(frameContainer)
        }

        val hTop = view.findViewByNames("handleMoveTop")
        val hBottom = view.findViewByNames("handleMoveBottom")
        val hLeft = view.findViewByNames("handleMoveLeft")
        val hRight = view.findViewByNames("handleMoveRight")

        if (frameContainer != null) {
            hTop?.let { setupIndependentViewDrag(it, frameContainer) }
            hBottom?.let { setupIndependentViewDrag(it, frameContainer) }
            hLeft?.let { setupIndependentViewDrag(it, frameContainer) }
            hRight?.let { setupIndependentViewDrag(it, frameContainer) }
        }

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && sq != null) {
            setupCornerResizeHandler(resizeHandle, sq)
        }

        return view
    }

    private fun setupIndependentViewDrag(touchView: View, targetViewToDrag: View = touchView) {
        var startTouchX = 0f
        var startTouchY = 0f
        var initialTranslationX = 0f
        var initialTranslationY = 0f

        touchView.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startTouchX = event.rawX
                    startTouchY = event.rawY
                    initialTranslationX = targetViewToDrag.translationX
                    initialTranslationY = targetViewToDrag.translationY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - startTouchX
                    val dy = event.rawY - startTouchY

                    targetViewToDrag.translationX = initialTranslationX + dx
                    targetViewToDrag.translationY = initialTranslationY + dy
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    true
                }
                else -> false
            }
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var lastTouchX = 0f
        var lastTouchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    lastTouchX = event.rawX
                    lastTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - lastTouchX).toInt()
                    val dy = (event.rawY - lastTouchY).toInt()

                    lastTouchX = event.rawX
                    lastTouchY = event.rawY

                    val location = IntArray(2)
                    targetSquare.getLocationOnScreen(location)
                    val squareX = location[0]
                    val squareY = location[1]

                    val maxW = (screenSize.x - squareX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - squareY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (currentFrameWidthPx + dx).coerceIn(minSizePx, maxW)
                    val newH = (currentFrameHeightPx + dy).coerceIn(minSizePx, maxH)

                    currentFrameWidthPx = newW
                    currentFrameHeightPx = newH

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
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
