package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class CandidateSelectionOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CANDIDATE_LAYER, OverlayPriority.HIGH) {

    private var activeCandidates = emptyList<MatchCandidate>()
    private var onCandidateConfirmed: ((MatchCandidate) -> Unit)? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
    }

    override fun createView(): View {
        return BeaconRadarCustomView(context)
    }

    fun showRadarBeaconCandidates(
        candidates: List<MatchCandidate>,
        callback: (MatchCandidate) -> Unit
    ) {
        this.activeCandidates = candidates
        this.onCandidateConfirmed = callback
        show()
        (overlayView as? BeaconRadarCustomView)?.setCandidates(candidates)
    }

    private inner class BeaconRadarCustomView(context: Context) : View(context) {

        private var candidateList = emptyList<MatchCandidate>()
        private var pulseRadius = 0f
        private var isIncreasing = true
        private val mainHandler = Handler(Looper.getMainLooper())

        private val pulseRunnable = object : Runnable {
            override fun run() {
                if (isIncreasing) {
                    pulseRadius += 2.0f
                    if (pulseRadius >= 16f) isIncreasing = false
                } else {
                    pulseRadius -= 2.0f
                    if (pulseRadius <= 0f) isIncreasing = true
                }
                invalidate()
                mainHandler.postDelayed(this, 30L)
            }
        }

        private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#FF00F5D4")
            style = Paint.Style.STROKE
            strokeWidth = 6f
        }

        private val pulsePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#8000E5FF")
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 32f
            isFakeBoldText = true
        }

        init {
            mainHandler.post(pulseRunnable)
        }

        fun setCandidates(list: List<MatchCandidate>) {
            this.candidateList = list
            invalidate()
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            for ((index, c) in candidateList.withIndex()) {
                val bbox = c.boundingBox
                val rectF = RectF(bbox)

                // Пульсирующий неоновый маяк вокруг найденной цели
                canvas.drawRoundRect(rectF, 12f, 12f, borderPaint)

                val pulseRect = RectF(
                    rectF.left - pulseRadius,
                    rectF.top - pulseRadius,
                    rectF.right + pulseRadius,
                    rectF.bottom + pulseRadius
                )
                canvas.drawRoundRect(pulseRect, 16f, 16f, pulsePaint)

                val scorePercent = "${(c.score * 100).toInt()}%"
                canvas.drawText("🎯 #${index + 1} ($scorePercent)", rectF.left, (rectF.top - 12f).coerceAtLeast(40f), textPaint)
            }
        }

        override fun onTouchEvent(event: MotionEvent): Boolean {
            if (event.action == MotionEvent.ACTION_DOWN) {
                val touchX = event.rawX
                val touchY = event.rawY

                // Тап по маяку на экране = Подтверждение выбора цели!
                for (c in candidateList) {
                    if (c.boundingBox.contains(touchX.toInt(), touchY.toInt())) {
                        logDiagnostic("AI_SCANNER", "Пользователь подтвердил цель тапом по экрану: ${c.point}")
                        onCandidateConfirmed?.invoke(c)
                        hide()
                        return true
                    }
                }
            }
            return super.onTouchEvent(event)
        }

        override fun onDetachedFromWindow() {
            super.onDetachedFromWindow()
            mainHandler.removeCallbacks(pulseRunnable)
        }
    }
}
