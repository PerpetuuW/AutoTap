package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import kotlin.math.abs

class TargetMarkerOverlay(
    context: Context,
    overlayManager: OverlayManager,
    val markerIndex: Int,
    val isEndMarker: Boolean = false
) : OverlayBase(context, overlayManager, OverlayLayer.TARGET_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = if (isEndMarker) R.layout.floating_target_end else R.layout.floating_target

    private var tvNumber: TextView? = null

    init {
        width = 44.dpToPx(context)
        height = 44.dpToPx(context)
        gravity = Gravity.TOP or Gravity.START
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        tvNumber = view.findViewByNames("tvTargetNumber", "tvTargetNumberEnd") as? TextView
        val label = if (isEndMarker) "${markerIndex + 1}E" else "${markerIndex + 1}"
        tvNumber?.text = label

        setupMarkerDragAndTap(view)
        return view
    }

    private fun setupMarkerDragAndTap(targetView: View) {
        var startX = 0f
        var startY = 0f
        var isDragging = false
        val touchSlop = 8.dpToPx(context)

        targetView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: return@setOnTouchListener false
            val svc = MyAutoClickService.instance ?: return@setOnTouchListener false
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = event.rawX
                    startY = event.rawY
                    isDragging = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - startX).toInt()
                    val dy = (event.rawY - startY).toInt()

                    if (!isDragging && (abs(dx) > touchSlop || abs(dy) > touchSlop)) {
                        isDragging = true
                    }

                    if (isDragging) {
                        val newX = (lp.x + dx).coerceIn(0, screenSize.x - width)
                        val newY = (lp.y + dy).coerceIn(0, screenSize.y - height)
                        updatePosition(newX, newY)

                        // Синхронизация координат с моделью шага в реальном времени
                        val actions = svc.actionsList
                        if (markerIndex in actions.indices) {
                            val action = actions[markerIndex]
                            val normX = (newX + width / 2f) / screenSize.x.toFloat()
                            val normY = (newY + height / 2f) / screenSize.y.toFloat()

                            if (isEndMarker) {
                                action.endXNorm = normX.coerceIn(0f, 1f)
                                action.endYNorm = normY.coerceIn(0f, 1f)
                            } else {
                                action.xNorm = normX.coerceIn(0f, 1f)
                                action.yNorm = normY.coerceIn(0f, 1f)
                            }
                        }

                        startX = event.rawX
                        startY = event.rawY
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    if (!isDragging) {
                        // Тач без перемещения = Нажатие на мишень для открытия настроек шага
                        overlayManager.editActionDialog.setTargetStepIndex(markerIndex)
                        overlayManager.editActionDialog.show()
                    }
                    isDragging = false
                    true
                }
                else -> false
            }
        }
    }
}
