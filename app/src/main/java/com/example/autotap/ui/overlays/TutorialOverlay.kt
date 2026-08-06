package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PointF
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Rect
import android.graphics.RectF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.dpToPx
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStepConfig
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class TutorialOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var currentStep: TutorialStepConfig? = null
    private var messageTextView: TextView? = null
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

        val card = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#EE1E1E2C"))
            setPadding(32, 32, 32, 32)
        }

        val tv = TextView(context).apply {
            text = "Инструкция туториала"
            setTextColor(Color.WHITE)
            textSize = 16f
            setPadding(0, 0, 0, 16)
        }
        messageTextView = tv
        card.addView(tv)

        val btnContainer = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
        }

        val btnNext = Button(context).apply {
            text = "Далее"
            setOnClickListener {
                logDiagnostic("TUTORIAL", "Нажата кнопка 'Далее' в туториале.")
                MyAutoClickService.instance?.tutorialEngine?.nextStep()
            }
        }
        btnContainer.addView(btnNext)

        val btnSkip = Button(context).apply {
            text = "Пропустить"
            setOnClickListener {
                logDiagnostic("TUTORIAL", "Туториал пропущен пользователем.")
                MyAutoClickService.instance?.tutorialEngine?.stopTutorial()
            }
        }
        btnContainer.addView(btnSkip)

        card.addView(btnContainer)

        val cardParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        ).apply {
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
            bottomMargin = 100.dpToPx(context)
        }

        root.addView(card, cardParams)
        return root
    }

    fun renderStep(step: TutorialStepConfig) {
        currentStep = step
        messageTextView?.text = step.message
        spotlightView?.setHighlightArea(step.highlightArea)
        logDiagnostic("TUTORIAL", "Отображение шага туториала: ${step.id}")
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
                return false // Пропускаем клик дальше к подлежащему элементу UI
            } else {
                logDiagnostic("TUTORIAL", "Клик вне целевой области туториала ($touchX, $touchY). Игнорируется.")
                return true // Поглощаем клик
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
