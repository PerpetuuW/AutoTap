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
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

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

        // ПРЯМАЯ ПРИВЯЗКА ПЕРЕТАСКИВАНИЯ К ЗНАЧКУ handleMoveFrame И ПЛАШКАМ
        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        val topBar = topBarView ?: view
        val bottomBar = bottomBarView ?: view
        val square = captureSquareView ?: view

        setupDragAndDrop(moveHandle)
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
        applyShiftingToolbarsRepositioning(x, y)
    }

    private fun applyShiftingToolbarsRepositioning(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val bottomBar = bottomBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val bottomBarHeight = bottomBar.height.takeIf { it > 0 } ?: 28.dpToPx(context)
        val squareHeight = square.height.takeIf { it > 0 } ?: 140.dpToPx(context)
        val gap = 4.dpToPx(context)

        val isNearTop = currentY <= (topBarHeight + 10.dpToPx(context))
        val isNearBottom = currentY >= (screenSize.y - squareHeight - bottomBarHeight - 60.dpToPx(context))

        when {
            isNearTop -> {
                topBar.translationY = (squareHeight + gap).toFloat()
                bottomBar.translationY = (squareHeight + topBarHeight + gap * 2).toFloat()
            }
            isNearBottom -> {
                bottomBar.translationY = -(squareHeight + bottomBarHeight + gap).toFloat()
                topBar.translationY = -(squareHeight + topBarHeight + bottomBarHeight + gap * 2).toFloat()
            }
            else -> {
                topBar.translationY = 0f
                bottomBar.translationY = 0f
            }
        }

        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 120.dpToPx(context)
        val bottomBarWidth = bottomBar.width.takeIf { it > 0 } ?: 90.dpToPx(context)
        val maxToolbarW = maxOf(topBarWidth, bottomBarWidth)

        if (square.width < maxToolbarW) {
            val extraWidth = maxToolbarW - square.width
            val isNearLeft = currentX <= extraWidth / 2
            val isNearRight = currentX >= screenSize.x - square.width - (extraWidth / 2)

            when {
                isNearLeft -> {
                    topBar.translationX = (extraWidth / 2f)
                    bottomBar.translationX = (extraWidth / 2f)
                }
                isNearRight -> {
                    topBar.translationX = -(extraWidth / 2f)
                    bottomBar.translationX = -(extraWidth / 2f)
                }
                else -> {
                    topBar.translationX = 0f
                    bottomBar.translationX = 0f
                }
            }
        } else {
            topBar.translationX = 0f
            bottomBar.translationX = 0f
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
