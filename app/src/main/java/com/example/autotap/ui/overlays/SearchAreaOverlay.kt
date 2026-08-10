package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Rect
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.LinearLayout
import com.example.autotap.CoordConverter
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class SearchAreaOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val minSizePx = 30.dpToPx(context)
    private var currentWidthPx = 200.dpToPx(context)
    private var currentHeightPx = 200.dpToPx(context)

    private var viewSearchAreaFrameView: View? = null
    private var topBarView: View? = null
    private var bottomBarView: View? = null

    init {
        gravity = Gravity.TOP or Gravity.START
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_search_area_frame, null)

        viewSearchAreaFrameView = view.findViewByNames("viewSearchAreaFrame")
        topBarView = view.findViewByNames("layoutSearchTopBar")
        bottomBarView = view.findViewByNames("layoutSearchBottomBar")

        view.bindClickByNames("btnSaveSearchArea") {
            val svc = MyAutoClickService.instance
            val frame = viewSearchAreaFrameView
            if (svc != null && frame != null) {
                val screenSize = context.getRealScreenSize()
                val location = IntArray(2)
                frame.getLocationOnScreen(location)

                val exactX = location[0]
                val exactY = location[1]
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
                    logDiagnostic("AI_SCANNER", "Зона поиска сохранена: ($exactX, $exactY, ${exactW}x${exactH}px), norm=$rectNorm")
                }
            }
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnResetSearchArea") {
            currentWidthPx = 200.dpToPx(context)
            currentHeightPx = 200.dpToPx(context)
            val frame = viewSearchAreaFrameView
            if (frame != null) {
                val lp = frame.layoutParams
                if (lp != null) {
                    lp.width = currentWidthPx
                    lp.height = currentHeightPx
                    frame.layoutParams = lp
                    frame.requestLayout()
                }
            }
            context.vibrateFeedback()
            logDiagnostic("AI_SCANNER", "Размер области поиска сброшен.")
        }

        view.bindClickByNames("btnCancelSearchArea", "btnCloseSearchArea") {
            hide()
        }

        val moveHandle = view.findViewByNames("handleMoveSearchArea") ?: view
        val topBar = topBarView ?: view
        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)

        val resizeHandle = view.findViewByNames("handleResizeSearchArea")
        val frameView = viewSearchAreaFrameView
        if (resizeHandle != null && frameView != null) {
            setupCornerResizeHandler(resizeHandle, frameView)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applyNonOverlappingToolbarRepositioning(x, y)
    }

    private fun applyNonOverlappingToolbarRepositioning(currentX: Int, currentY: Int) {
        val frame = viewSearchAreaFrameView ?: return
        val topBar = topBarView ?: return
        val bottomBar = bottomBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val bottomBarHeight = bottomBar.height.takeIf { it > 0 } ?: 28.dpToPx(context)
        val squareHeight = frame.height.takeIf { it > 0 } ?: 200.dpToPx(context)
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

        if (frame.width < maxToolbarW) {
            val extraWidth = maxToolbarW - frame.width
            val isNearLeft = currentX <= extraWidth / 2
            val isNearRight = currentX >= screenSize.x - frame.width - (extraWidth / 2)

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

    private fun setupCornerResizeHandler(resizeView: View, targetFrame: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetFrame.width.takeIf { it > 0 } ?: currentWidthPx
                    startH = targetFrame.height.takeIf { it > 0 } ?: currentHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    targetFrame.getLocationOnScreen(location)
                    val windowX = location[0]
                    val windowY = location[1]

                    val maxW = (screenSize.x - windowX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - windowY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (startW + dx).coerceIn(minSizePx, maxW)
                    val newH = (startH + dy).coerceIn(minSizePx, maxH)

                    currentWidthPx = newW
                    currentHeightPx = newH

                    val lp = targetFrame.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetFrame.layoutParams = lp
                        targetFrame.requestLayout()
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
