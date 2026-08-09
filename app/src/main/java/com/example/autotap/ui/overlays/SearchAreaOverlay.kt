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

        val handle = view.findViewByNames("handleMoveSearchArea", "layoutSearchBottomBar") ?: view
        setupDragAndDrop(handle)

        val resizeHandle = view.findViewByNames("handleResizeSearchArea")
        val frameView = viewSearchAreaFrameView
        if (resizeHandle != null && frameView != null) {
            setupCornerResizeHandler(resizeHandle, frameView)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applyEdgeSnappingAlignment(x)
    }

    private fun applyEdgeSnappingAlignment(currentX: Int) {
        val frame = viewSearchAreaFrameView ?: return
        val screenSize = context.getRealScreenSize()
        val lp = frame.layoutParams as? LinearLayout.LayoutParams ?: return

        val leftThreshold = 60.dpToPx(context)
        val rightThreshold = screenSize.x - 140.dpToPx(context)

        val newGravity = when {
            currentX <= leftThreshold -> Gravity.START
            currentX >= rightThreshold -> Gravity.END
            else -> Gravity.CENTER_HORIZONTAL
        }

        if (lp.gravity != newGravity) {
            lp.gravity = newGravity
            frame.layoutParams = lp
            frame.requestLayout()
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetFrame: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val root = rootView ?: return@setOnTouchListener false
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetFrame.width
                    startH = targetFrame.height
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

                    currentWidthPx = (startW + dx).coerceIn(minSizePx, maxW)
                    currentHeightPx = (startH + dy).coerceIn(minSizePx, maxH)

                    val lp = targetFrame.layoutParams
                    if (lp != null) {
                        lp.width = currentWidthPx
                        lp.height = currentHeightPx
                        targetFrame.layoutParams = lp
                        targetFrame.requestLayout()
                    }
                    true
                }
                else -> false
            }
        }
    }
}
