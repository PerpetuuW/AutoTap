package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import com.example.autotap.R
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager

class CandidateSelectionOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var candidatesContainer: LinearLayout? = null
    private var onCandidateSelected: ((MatchCandidate) -> Unit)? = null

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CANDIDATE_LAYER
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.candidate_selection_overlay, null)

        candidatesContainer = view.findViewByNames("candidateContainer") as? LinearLayout
        return view
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
