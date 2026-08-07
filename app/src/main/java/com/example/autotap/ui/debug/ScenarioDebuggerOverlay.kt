package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.findViewByNames
import com.example.autotap.logAppEvent
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null
    private var tvCandidatePercentView: TextView? = null
    private var viewCandidateBorderView: View? = null
    private var ivHeatmap: ImageView? = null

    init {
        width = 600
        height = 400
        gravity = Gravity.TOP or Gravity.END
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#AA000000"))
            setPadding(16, 16, 16, 16)

            val tv = TextView(context).apply {
                text = "Scenario Debugger: Готов"
                setTextColor(Color.GREEN)
                textSize = 14f
            }
            statusText = tv
            addView(tv)

            val img = ImageView(context).apply {
                visibility = View.GONE
            }
            ivHeatmap = img
            addView(img, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                200
            ))
        }

        val inflater = LayoutInflater.from(context)
        try {
            val calibBox = inflater.inflate(R.layout.floating_calibration_box, null)
            tvCandidatePercentView = calibBox.findViewByNames("tvCandidatePercent") as? TextView
            viewCandidateBorderView = calibBox.findViewByNames("viewCandidateBorder")
            root.addView(calibBox)
        } catch (_: Exception) {}

        return root
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        val scorePercent = if (candidates.isNotEmpty()) "${(candidates.first().score * 100).toInt()}%" else "0%"
        statusText?.text = "Кандидатов найдено: ${candidates.size} ($scorePercent)"
        tvCandidatePercentView?.text = scorePercent
        logAppEvent("AI_SCANNER", "Debugger: кандидатов ${candidates.size}")
    }

    fun showHeatmap(heatmap: Bitmap) {
        ivHeatmap?.setImageBitmap(heatmap)
        ivHeatmap?.visibility = View.VISIBLE
    }

    fun showNoMatch() {
        statusText?.text = "NO MATCH: Совпадения не найдены"
        tvCandidatePercentView?.text = "0%"
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")
    }
}
