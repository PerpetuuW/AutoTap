package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.findViewByNames
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager

class TargetMarkerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var tvNumber: TextView? = null
    private var tvEndNumber: TextView? = null

    init {
        gravity = Gravity.TOP or Gravity.START
        layer = OverlayLayer.VISUALIZER_LAYER
    }

    override fun createView(): View {
        val container = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }

        val inflater = LayoutInflater.from(context)
        val startView = try {
            inflater.inflate(R.layout.floating_target, null)
        } catch (e: Exception) {
            View(context)
        }
        tvNumber = startView.findViewByNames("tvTargetNumber") as? TextView
        container.addView(startView)

        try {
            val endView = inflater.inflate(R.layout.floating_target_end, null)
            tvEndNumber = endView.findViewByNames("tvTargetNumberEnd") as? TextView
            container.addView(endView)
        } catch (_: Exception) {}

        return container
    }

    fun setTargetNumber(num: Int) {
        val textStr = num.toString()
        tvNumber?.text = textStr
        tvEndNumber?.text = "${textStr}E"
    }
}
