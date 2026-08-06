package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class CandidateSelectionOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var candidatesContainer: LinearLayout? = null
    private var onCandidateSelected: ((MatchCandidate) -> Unit)? = null

    init {
        gravity = Gravity.CENTER
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#DD000000"))
            setPadding(32, 32, 32, 32)
        }

        val title = TextView(context).apply {
            text = "Выберите цель"
            setTextColor(Color.WHITE)
            textSize = 16f
        }
        root.addView(title)

        val container = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
        }
        candidatesContainer = container
        root.addView(container)

        return root
    }

    fun showCandidates(candidates: List<MatchCandidate>, callback: (MatchCandidate) -> Unit) {
        this.onCandidateSelected = callback
        show()

        val container = candidatesContainer ?: return
        container.removeAllViews()

        for ((index, candidate) in candidates.withIndex()) {
            val btn = Button(context).apply {
                text = "Цель #${index + 1} (score: ${"%.2f".format(candidate.score)})"
                setOnClickListener {
                    logDiagnostic("AI_SCANNER", "Выбрана цель #${index + 1}")
                    onCandidateSelected?.invoke(candidate)
                    hide()
                }
            }
            container.addView(btn)
        }
    }
}
