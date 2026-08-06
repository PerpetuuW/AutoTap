package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logAppEvent
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null

    init {
        width = 600
        height = 400
        gravity = Gravity.TOP or Gravity.END
    }

    override fun createView(): View {
        return LinearLayout(context).apply {
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
        }
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        statusText?.text = "Кандидатов найдено: ${candidates.size}"
        logAppEvent("AI_SCANNER", "Debugger: кандидатов ${candidates.size}")
    }

    fun showNoMatch() {
        statusText?.text = "NO MATCH: Совпадения не найдены"
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")
    }
}
