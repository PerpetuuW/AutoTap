package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Rect
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import com.example.autotap.CoordConverter
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

class SearchAreaOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val minSizePx = 32.dpToPx(context)
    private var currentWidthPx = 200.dpToPx(context)
    private var currentHeightPx = 200.dpToPx(context)

    private var viewSearchAreaFrameView: View? = null

    init {
        gravity = Gravity.TOP or Gravity.START
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = currentWidthPx
        height = currentHeightPx
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_search_area_frame, null)

        viewSearchAreaFrameView = view.findViewByNames("viewSearchAreaFrame")

        view.bindClickByNames("btnSaveSearchArea") {
            val svc = MyAutoClickService.instance
            val lp = layoutParams
            val frame = viewSearchAreaFrameView
            if (svc != null && lp != null && frame != null) {
                val screenSize = context.getRealScreenSize()

                val exactX = lp.x + frame.left
                val exactY = lp.y + frame.top
                val exactW = frame.width.takeIf { it > 0 } ?: currentWidthPx
                val exactH = frame.height.takeIf { it > 0 } ?: currentHeightPx

                val rectPx = Rect(exactX, exactY, exactX + exactW, exactY + exactH)
                val rectNorm = CoordConverter.toNormalizedRect(rectPx, screenSize.x, screenSize.y)

                if (svc.actionsList.isNotEmpty()) {
                    val currentAction = svc.actionsList.last()
                    currentAction.customSearchArea = true
                    currentAction.searchAreaX = exactX
                    currentAction.searchAreaY = exactY
                    currentAction.searchAreaW = exactW
                    currentAction.searchAreaH = exactH
                    logDiagnostic("AI_SCANNER", "Зона поиска сохранена с точным смещением рамки: ($exactX, $exactY, ${exactW}x${exactH}px), norm=$rectNorm")
                }
            }
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnResetSearchArea") {
            currentWidthPx = 200.dpToPx(context)
            currentHeightPx = 200.dpToPx(context)
            width = currentWidthPx
            height = currentHeightPx
            val lp = layoutParams
            val targetView = overlayView
            if (lp != null && targetView != null) {
                lp.width = currentWidthPx
                lp.height = currentHeightPx
                try {
                    windowManager.updateViewLayout(targetView, lp)
                } catch (e: Exception) {
                    logError("OVERLAY", "Ошибка обновления расположения в btnResetSearchArea", e)
                }
            }
            context.vibrateFeedback()
            logDiagnostic("AI_SCANNER", "Размер области поиска сброшен к 200x200px.")
        }

        view.bindClickByNames("btnCancelSearchArea", "btnCloseSearchArea") {
            logDiagnostic("AI_SCANNER", "Настройка области поиска отменена пользователем.")
            hide()
        }

        val handle = view.findViewByNames("handleMoveSearchArea", "layoutSearchTopBar") ?: view
        setupDragAndDrop(handle)

        val resizeHandle = view.findViewByNames("handleResizeSearchArea")
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
            val targetView = overlayView ?: return@setOnTouchListener false
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
                    width = currentWidthPx
                    height = currentHeightPx

                    try {
                        windowManager.updateViewLayout(targetView, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка ресайза области поиска", e)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
