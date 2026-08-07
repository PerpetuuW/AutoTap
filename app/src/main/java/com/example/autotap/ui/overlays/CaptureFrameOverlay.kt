package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.graphics.PointF
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
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

    private var layoutCaptureContainer: LinearLayout? = null
    private var layoutTopBar: View? = null
    private var layoutBottomBar: View? = null
    private var captureSquare: FrameLayout? = null

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

        layoutCaptureContainer = view.findViewByNames("layoutCaptureContainer") as? LinearLayout
        layoutTopBar = view.findViewByNames("layoutTopBar")
        layoutBottomBar = view.findViewByNames("layoutBottomBar")
        captureSquare = view.findViewByNames("captureSquare") as? FrameLayout

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски с экрана (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val lp = layoutParams ?: params
            val square = captureSquare
            if (svc != null && lp != null && square != null) {
                val fullBitmap = svc.captureScreenBitmap()
                if (fullBitmap != null && fullBitmap.width > 20 && fullBitmap.height > 20) {
                    // АБСОЛЮТНЫЙ РАСЧЕТ КООРДИНАТ КВАДРАТА ПРИЦЕЛА НА ЭКРАНЕ
                    val squareLeftOnScreen = lp.x + square.left
                    val squareTopOnScreen = lp.y + square.top

                    val safeX = squareLeftOnScreen.coerceIn(0, (fullBitmap.width - 20).coerceAtLeast(0))
                    val safeY = squareTopOnScreen.coerceIn(0, (fullBitmap.height - 20).coerceAtLeast(0))
                    val safeW = currentFrameWidthPx.coerceIn(10, fullBitmap.width - safeX)
                    val safeH = currentFrameHeightPx.coerceIn(10, fullBitmap.height - safeY)

                    val metrics = context.resources.displayMetrics
                    val centerXNorm = (safeX + safeW / 2f) / metrics.widthPixels.toFloat()
                    val centerYNorm = (safeY + safeH / 2f) / metrics.heightPixels.toFloat()

                    val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                    val action = ActionConfig(
                        type = ActionType.AI_SEARCH,
                        xNorm = centerXNorm.coerceIn(0f, 1f),
                        yNorm = centerYNorm.coerceIn(0f, 1f),
                        selectedTemplateIndex = nextTemplateIndex
                    )
                    svc.actionsList.add(action)

                    if (safeW > 10 && safeH > 10) {
                        val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                        svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)
                        logDiagnostic("AI_SCANNER", "Безопасный точный кроп: шаблон #$nextTemplateIndex сохранен (${safeW}x${safeH}px).")

                        val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                        if (calibrated != null) {
                            overlayManager.debuggerOverlay.show()
                            overlayManager.debuggerOverlay.showCandidates(listOf(
                                com.example.autotap.engine.ai.MatchCandidate(
                                    point = PointF(safeX + safeW / 2f, safeY + safeH / 2f),
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
        val squareW = currentFrameWidthPx
        val squareH = currentFrameHeightPx

        // Разрешаем прицелу подходить вплотную к 0-границе экрана
        val topOffset = layoutTopBar?.height ?: 120
        val minX = -50
        val minY = -topOffset
        val maxX = screenSize.x - 50
        val maxY = screenSize.y - 50

        lp.x = x.coerceIn(minX, maxX)
        lp.y = y.coerceIn(minY, maxY)

        // УМНОЕ АВТО-ПОЗИЦИОНИРОВАНИЕ ПАНЕЛЕЙ КНОПОК ПРИ ПРИБЛИЖЕНИИ К КРАЯМ
        applySmartPanelFlipping(lp.y, screenSize.y)

        val v = overlayView ?: rootView ?: return
        try {
            windowManager.updateViewLayout(v, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления позиции прицела", e)
        }
    }

    private fun applySmartPanelFlipping(currentY: Int, screenHeight: Int) {
        val container = layoutCaptureContainer ?: return
        val topBar = layoutTopBar ?: return
        val bottomBar = layoutBottomBar ?: return
        val square = captureSquare ?: return

        container.removeAllViews()

        if (currentY < 120) {
            // ВЕРХНИЙ КРАЙ: Верхняя панель переворачивается И ПОДСТАВЛЯЕТСЯ ПОД ПРИЦЕЛ
            container.addView(square)
            container.addView(topBar)
            container.addView(bottomBar)
        } else if (currentY > screenHeight - (currentFrameHeightPx + 200)) {
            // НИЖНИЙ КРАЙ: Нижняя панель поднимается НАД ПРИЦЕЛОМ
            container.addView(topBar)
            container.addView(bottomBar)
            container.addView(square)
        } else {
            // О Б Ы Ч Н Ы Й   Р Е Ж И М
            container.addView(topBar)
            container.addView(square)
            container.addView(bottomBar)
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
