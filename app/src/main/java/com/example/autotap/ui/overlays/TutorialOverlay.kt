package com.example.autotap.ui.overlays

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStep
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class TutorialOverlay(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, OverlayLayer.TUTORIAL_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.floating_tutorial_overlay

    private var currentStep = 0
    private var steps: List<TutorialStep> = emptyList()
    private var onFinishCallback: (() -> Unit)? = null

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        return inflater.inflate(layoutResId, null)
    }

    fun startTutorial(stepsList: List<TutorialStep>, onFinish: (() -> Unit)? = null) {
        this.steps = stepsList
        this.onFinishCallback = onFinish
        this.currentStep = 0
        show()
        if (steps.isNotEmpty()) {
            showStep(0)
        }
    }

    private fun showStep(index: Int) {
        val v = rootView ?: return
        val spotlight = v.findViewById<View>(R.id.tutorialSpotlight)
        val arrow = v.findViewById<ImageView>(R.id.tutorialArrow)
        val hintCard = v.findViewById<LinearLayout>(R.id.tutorialHintCard)
        val hintText = v.findViewById<TextView>(R.id.tutorialHintText)
        val btnNext = v.findViewById<Button>(R.id.tutorialNextButton)

        if (index !in steps.indices) return
        val step = steps[index]

        if (step.spotlightX != null && step.spotlightY != null) {
            spotlight?.visibility = View.VISIBLE
            spotlight?.translationX = step.spotlightX.toFloat() - (spotlight?.width ?: 0) / 2f
            spotlight?.translationY = step.spotlightY.toFloat() - (spotlight?.height ?: 0) / 2f
        } else {
            spotlight?.visibility = View.GONE
        }

        if (step.arrowX != null && step.arrowY != null) {
            arrow?.visibility = View.VISIBLE
            arrow?.translationX = step.arrowX.toFloat()
            arrow?.translationY = step.arrowY.toFloat()
        } else {
            arrow?.visibility = View.GONE
        }

        hintCard?.visibility = View.VISIBLE
        hintCard?.translationX = step.hintX.toFloat()
        hintCard?.translationY = step.hintY.toFloat()
        hintText?.text = step.hintText

        btnNext?.setOnClickListener {
            currentStep++
            if (currentStep >= steps.size) {
                hide()
                onFinishCallback?.invoke()
                logDiagnostic("TUTORIAL", "Интерактивный туториал завершен.")
            } else {
                showStep(currentStep)
            }
        }
    }
}
