package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Rect
import android.graphics.RectF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStepConfig
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class TutorialOverlay(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, overlayManager, OverlayLayer.TUTORIAL_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.floating_tutorial_card

    private var currentStep: TutorialStepConfig? = null
    private var tvTitleView: TextView? = null
    private var tvDescView: TextView? = null
    private var spotlightView: SpotlightCustomView? = null
    private var tutorialCardView: View? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
        initialX = 0
        initialY = 0
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
            inflater.inflate(layoutResId, null)
        } catch (e: Exception) {
            View(context)
        }
        tutorialCardView = card

        tvTitleView = card.findViewByNames("tvTutTitle") as? TextView
        tvDescView = card.findViewByNames("tvTutDesc") as? TextView

        card.bindClickByNames("btnTutNext") {
            logDiagnostic("TUTORIAL", "Нажата btnTutNext.")
            MyAutoClickService.instance?.tutorialEngine?.nextStep()
        }

        card.bindClickByNames("btnTutPrev") {
            logDiagnostic("TUTORIAL", "Нажата btnTutPrev.")
            MyAutoClickService.instance?.tutorialEngine?.previousStep()
        }

        card.bindClickByNames("btnTutSkip") {
            logDiagnostic("TUTORIAL", "Нажата btnTutSkip.")
            MyAutoClickService.instance?.tutorialEngine?.stopTutorial()
        }

        val cardParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        ).apply {
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
            marginStart = 24.dpToPx(context)
            marginEnd = 24.dpToPx(context)
            bottomMargin = 48.dpToPx(context)
        }

        root.addView(card, cardParams)
        return root
    }

    fun renderStep(step: TutorialStepConfig) {
        currentStep = step
        tvTitleView?.text = step.title
        tvDescView?.text = step.message
        spotlightView?.setHighlightArea(step.highlightArea)

        val card = tutorialCardView
        val highlight = step.highlightArea
        if (card != null && highlight != null) {
            val lp = card.layoutParams as? FrameLayout.LayoutParams
            if (lp != null) {
                val screenSize = context.getRealScreenSize()
                if (highlight.top < screenSize.y / 2) {
                    lp.gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                    lp.topMargin = (highlight.bottom + 16.dpToPx(context)).coerceAtMost(screenSize.y - 200.dpToPx(context))
                    lp.bottomMargin = 0
                } else {
                    lp.gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
                    lp.bottomMargin = (screenSize.y - highlight.top + 16.dpToPx(context)).coerceAtMost(screenSize.y - 200.dpToPx(context))
                    lp.topMargin = 0
                }
                card.layoutParams = lp
            }
        }
        logDiagnostic("TUTORIAL", "Отображение туториала: ${step.title}")
    }

    private fun handleTouchInTutorial(event: MotionEvent): Boolean {
        val step = currentStep ?: return false
        val targetArea = step.waitForClickOnArea ?: step.highlightArea

        if (event.action == MotionEvent.ACTION_DOWN) {
            val touchX = event.rawX.toInt()
            val touchY = event.rawY.toInt()

            val card = tutorialCardView
            if (card != null) {
                val cardLoc = IntArray(2)
                card.getLocationOnScreen(cardLoc)
                val cardRect = Rect(cardLoc[0], cardLoc[1], cardLoc[0] + card.width, cardLoc[1] + card.height)
                if (cardRect.contains(touchX, touchY)) {
                    return false
                }
            }

            if (targetArea != null && targetArea.contains(touchX, touchY)) {
                logDiagnostic("TUTORIAL", "Клик попал в целевую область ($touchX, $touchY).")
                MyAutoClickService.instance?.tutorialEngine?.nextStep()
                return false
            } else {
                logDiagnostic("TUTORIAL", "Клик вне целевой области ($touchX, $touchY). Игнорируется.")
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
        private var pulseRadius = 0f
        private var pulseIncreasing = true
        private val handler = Handler(Looper.getMainLooper())

        private val pulseRunnable = object : Runnable {
            override fun run() {
                if (pulseIncreasing) {
                    pulseRadius += 1.5f
                    if (pulseRadius >= 14f) pulseIncreasing = false
                } else {
                    pulseRadius -= 1.5f
                    if (pulseRadius <= 0f) pulseIncreasing = true
                }
                invalidate()
                handler.postDelayed(this, 30L)
            }
        }

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

        private val pulsePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#8000F5D4")
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        init {
            setLayerType(LAYER_TYPE_SOFTWARE, null)
            handler.post(pulseRunnable)
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

                val pulseRect = RectF(
                    rect.left - pulseRadius,
                    rect.top - pulseRadius,
                    rect.right + pulseRadius,
                    rect.bottom + pulseRadius
                )
                canvas.drawRoundRect(pulseRect, 20f, 20f, pulsePaint)
            }
        }

        override fun onTouchEvent(event: MotionEvent): Boolean {
            val handled = onTouchEventCallback(event)
            return handled || super.onTouchEvent(event)
        }

        override fun onDetachedFromWindow() {
            super.onDetachedFromWindow()
            handler.removeCallbacks(pulseRunnable)
        }
    }
}
