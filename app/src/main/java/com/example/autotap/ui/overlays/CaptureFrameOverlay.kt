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
    private var bottomBarView: View? = null

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
        bottomBarView = view.findViewByNames("layoutBottomBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val square = captureSquareView
            val root = rootView

            if (svc != null && square != null && root != null) {
                // Скрываем оверлей для чистого скриншота без заставок
                root.visibility = View.INVISIBLE

                mainHandler.postDelayed({
                    svc.captureScreenBitmapAsync { fullBitmap ->
                        root.visibility = View.VISIBLE
                        if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                            val location = IntArray(2)
                            square.getLocationOnScreen(location)
                            val safeX = location[0].coerceIn(0, (fullBitmap.width - 10).coerceAtLeast(0))
                            val safeY = location[1].coerceIn(0, (fullBitmap.height - 10).coerceAtLeast(0))

                            val maxAllowedW = fullBitmap.width - safeX
                            val maxAllowedH = fullBitmap.height - safeY
                            val safeW = square.width.coerceIn(5, maxAllowedW)
                            val safeH = square.height.coerceIn(5, maxAllowedH)

                            val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                            if (safeW > 5 && safeH > 5) {
                                try {
                                    val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                                    svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                    val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                                    if (calibrated != null) {
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

        // Перетаскивание за ЛЮБУЮ ЧАСТЬ кадра
        val topBar = topBarView ?: view
        val bottomBar = bottomBarView ?: view
        val square = captureSquareView ?: view

        setupDragAndDrop(topBar)
        setupDragAndDrop(bottomBar)
        setupDragAndDrop(square)

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && captureSquareView != null) {
            setupCornerResizeHandler(resizeHandle, captureSquareView!!)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applySmartEdgeFlipping(x, y)
    }

    private fun applySmartEdgeFlipping(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val bottomBar = bottomBarView ?: return
        val screenSize = context.getRealScreenSize()

        // 1. АВТО-УКЛОНЕНИЕ ТУЛБАРОВ У ВЕРХНЕГО И НИЖНЕГО КРАЕВ
        val isNearTop = currentY <= 50.dpToPx(context)
        val isNearBottom = currentY >= screenSize.y - 180.dpToPx(context)

        topBar.translationY = if (isNearTop) (square.height + 40.dpToPx(context)).toFloat() else 0f
        bottomBar.translationY = if (isNearBottom) -(square.height + 40.dpToPx(context)).toFloat() else 0f

        // 2. ДИНАМИЧЕСКОЕ ПРИЛИПАНИЕ РАМКИ ВЛЕВО И ВПРАВО
        val lp = square.layoutParams as? LinearLayout.LayoutParams ?: return
        val leftThreshold = 60.dpToPx(context)
        val rightThreshold = screenSize.x - 140.dpToPx(context)

        val newGravity = when {
            currentX <= leftThreshold -> Gravity.START
            currentX >= rightThreshold -> Gravity.END
            else -> Gravity.CENTER_HORIZONTAL
        }

        if (lp.gravity != newGravity) {
            lp.gravity = newGravity
            square.layoutParams = lp
            square.requestLayout()
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val root = rootView ?: return@setOnTouchListener false
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetSquare.width
                    startH = targetSquare.height
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    root.getLocationOnScreen(location)
                    val windowX = location[0]
                    val windowY = location[1]

                    val maxW = (screenSize.x - windowX - 8.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - windowY - 80.dpToPx(context)).coerceAtLeast(minSizePx)

                    currentFrameWidthPx = (startW + dx).coerceIn(minSizePx, maxW)
                    currentFrameHeightPx = (startH + dy).coerceIn(minSizePx, maxH)

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = currentFrameWidthPx
                        lp.height = currentFrameHeightPx
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
                    }
                    true
                }
                else -> false
            }
        }
    }
}
