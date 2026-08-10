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
import android.widget.LinearLayout
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

    private val minSizePx = 20.dpToPx(context)
    private var currentFrameWidthPx = 140.dpToPx(context)
    private var currentFrameHeightPx = 140.dpToPx(context)

    private var captureSquareView: View? = null
    private var topBarView: View? = null

    private val mainHandler = Handler(Looper.getMainLooper())

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

        captureSquareView = view.findViewByNames("captureSquare")
        topBarView = view.findViewByNames("layoutTopBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture") {
            logDiagnostic("CAPTURE_FRAME", "Снятие шаблона (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val square = captureSquareView
            val root = rootView

            if (svc != null && square != null && root != null) {
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

                val screenSize = context.getRealScreenSize()
                val cropNormX = ((cropX + cropW / 2f) / screenSize.x.toFloat()).coerceIn(0f, 1f)
                val cropNormY = ((cropY + cropH / 2f) / screenSize.y.toFloat()).coerceIn(0f, 1f)

                root.visibility = View.INVISIBLE

                mainHandler.postDelayed({
                    svc.captureScreenBitmapAsync { fullBitmap ->
                        root.visibility = View.VISIBLE
                        if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                            val safeX = cropX.coerceIn(0, (fullBitmap.width - 10).coerceAtLeast(0))
                            val safeY = cropY.coerceIn(0, (fullBitmap.height - 10).coerceAtLeast(0))

                            val maxAllowedW = fullBitmap.width - safeX
                            val maxAllowedH = fullBitmap.height - safeY
                            val safeW = cropW.coerceIn(5, maxAllowedW)
                            val safeH = cropH.coerceIn(5, maxAllowedH)

                            val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                            if (safeW > 5 && safeH > 5) {
                                try {
                                    val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
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
                                        safeW,
                                        safeH
                                    )
                                } catch (e: Exception) {
                                    logError("CAPTURE_FRAME", "Ошибка создания Bitmap кропа маски", e)
                                }
                            }
                        }
                    }
                    hide()
                    overlayManager.showControlPanel()
                }, 120L)
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

        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        val topBar = topBarView ?: view

        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)

        val sq = captureSquareView
        if (sq != null) {
            setupDragAndDrop(sq)
        }

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && sq != null) {
            setupCornerResizeHandler(resizeHandle, sq)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        updateDynamicToolbarDocking(x, y)
    }

    // 💥 ДИНАМИЧЕСКИЙ РАСЧЕТ ПРИЛИПАНИЯ ТУЛБАРА К КРАЯМ ЭКРАНА
    private fun updateDynamicToolbarDocking(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 180.dpToPx(context)
        val squareWidth = square.width.takeIf { it > 0 } ?: currentFrameWidthPx
        val squareHeight = square.height.takeIf { it > 0 } ?: currentFrameHeightPx
        val gap = 6.dpToPx(context)

        // 1. ВЕРТИКАЛЬНАЯ ПРОВЕРКА (Если уперлись в самый ВЕРХ -> Тулбар прыгает ПОД рамку)
        if (currentY < (topBarHeight + gap)) {
            topBar.translationY = (squareHeight + gap * 2).toFloat()
        } else {
            topBar.translationY = 0f
        }

        // 2. ГОРИЗОНТАЛЬНАЯ ПРОВЕРКА (Смещение к центру, чтобы кнопки не уходили за экран)
        val idealX = currentX + (squareWidth - topBarWidth) / 2
        val clampedX = idealX.coerceIn(0, (screenSize.x - topBarWidth).coerceAtLeast(0))
        topBar.translationX = (clampedX - currentX).toFloat()
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetSquare.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = targetSquare.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    targetSquare.getLocationOnScreen(location)
                    val squareX = location[0]
                    val squareY = location[1]

                    val maxW = (screenSize.x - squareX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - squareY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (startW + dx).coerceIn(minSizePx, maxW)
                    val newH = (startH + dy).coerceIn(minSizePx, maxH)

                    currentFrameWidthPx = newW
                    currentFrameHeightPx = newH

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
                    }
                    val currentLp = layoutParams ?: params
                    if (currentLp != null) {
                        updateDynamicToolbarDocking(currentLp.x, currentLp.y)
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
