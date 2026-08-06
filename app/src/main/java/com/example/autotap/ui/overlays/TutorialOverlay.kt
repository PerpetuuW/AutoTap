package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Rect
import android.graphics.RectF
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.widget.FrameLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStepConfig
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class TutorialOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var currentStep: TutorialStepConfig? = null
    private var tvTitleView: TextView? = null
    private var tvDescView: TextView? = null
    private var spotlightView: SpotlightCustomView? = null

    init {
        width = FrameLayout.LayoutParams.MATCH_PARENT
        height = FrameLayout.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
        initialX = 0
        initialY = 0
        layer = OverlayLayer.TUTORIAL_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val root = FrameLayout(context)

        val customSpotlight = SpotlightCustomView(context) { event ->
            handleTouchInTutorial(event)
        }
        spotlightView = customSpotlight
        root.addView(customSpotlight, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ))

        val inflater = LayoutInflater.from(context)
        val card = try {
            inflater.inflate(R.layout.floating_tutorial_card, null)
        } catch (e: Exception) {
            View(context)
        }

        tvTitleView = card.findViewByNames("tvTutTitle") as? TextView
        tvDescView = card.findViewByNames("tvTutDesc") as? TextView

        card.bindClickByNames("btnTutNext") {
            logDiagnostic("TUTORIAL", "Нажата btnTutNext в floating_tutorial_card.")
            MyAutoClickService.instance?.tutorialEngine?.nextStep()
        }

        card.bindClickByNames("btnTutPrev") {
            logDiagnostic("TUTORIAL", "Нажата btnTutPrev в floating_tutorial_card.")
        }

        card.bindClickByNames("btnTutSkip") {
            logDiagnostic("TUTORIAL", "Нажата btnTutSkip в floating_tutorial_card.")
            MyAutoClickService.instance?.tutorialEngine?.stopTutorial()
        }

        val cardParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        ).apply {
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        }

        root.addView(card, cardParams)
        return root
    }

    fun renderStep(step: TutorialStepConfig) {
        currentStep = step
        tvTitleView?.text = step.id
        tvDescView?.text = step.message
        spotlightView?.setHighlightArea(step.highlightArea)
        logDiagnostic("TUTORIAL", "Отображение туториала: ${step.id}")
    }

    private fun handleTouchInTutorial(event: MotionEvent): Boolean {
        val step = currentStep ?: return false
        val targetArea = step.waitForClickOnArea ?: step.highlightArea

        if (event.action == MotionEvent.ACTION_DOWN) {
            val touchX = event.rawX.toInt()
            val touchY = event.rawY.toInt()

            if (targetArea != null && targetArea.contains(touchX, touchY)) {
                logDiagnostic("TUTORIAL", "Клик попал в целевую область туториала ($touchX, $touchY).")
                MyAutoClickService.instance?.tutorialEngine?.nextStep()
                return false
            } else {
                logDiagnostic("TUTORIAL", "Клик вне целевой области туториала ($touchX, $touchY). Игнорируется.")
                return true
            }
        }
        return false
    }

    private class SpotlightCustomView(
        context: Context,
        private val onTouchEventCallback: (MotionEvent) -> Boolean
    ) : View(context) {

        private var highlightArea: Rect? = null

        private val dimPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#B3000000")
            style = Paint.Style.FILL
        }

        private val clearPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            xfermode = PorterDuffXfermode(PorterDuff.Mode.CLEAR)
        }

        private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#FF00E676")
            style = Paint.Style.STROKE
            strokeWidth = 6f
        }

        init {
            setLayerType(LAYER_TYPE_SOFTWARE, null)
        }

        fun setHighlightArea(rect: Rect?) {
            highlightArea = rect
            invalidate()
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), dimPaint)

            val rect = highlightArea
            if (rect != null) {
                val rectF = RectF(rect)
                canvas.drawRoundRect(rectF, 16f, 16f, clearPaint)
                canvas.drawRoundRect(rectF, 16f, 16f, borderPaint)
            }
        }

        override fun onTouchEvent(event: MotionEvent): Boolean {
            val handled = onTouchEventCallback(event)
            return handled || super.onTouchEvent(event)
        }
    }
}
