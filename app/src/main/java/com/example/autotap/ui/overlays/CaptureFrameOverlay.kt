package com.example.autotap.ui.overlays

import android.graphics.Bitmap
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import android.widget.Toast
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class CaptureFrameOverlay(
    private val service: MyAutoClickService,
    val overlayManager: OverlayManager = service.overlayManager
) {

    private var rootView: View? = null

    fun show() {
        if (rootView != null) return

        val view = LayoutInflater.from(service)
            .inflate(R.layout.floating_capture_frame, null)
        rootView = view

        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }

        bindUi(view)
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }

    fun startRecording() {
        show()
        service.isRecording = true
    }

    private fun bindUi(view: View) {
        val captureSquare = view.findViewById<View>(R.id.captureSquare)
        val layoutTopBar = view.findViewById<View>(R.id.layoutTopBar)
        val layoutBottomBar = view.findViewById<View>(R.id.layoutBottomBar)

        val handleMove = view.findViewById<View>(R.id.handleMoveFrame)
        val handleResize = view.findViewById<View>(R.id.handleResize)

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnSearchArea = view.findViewById<Button>(R.id.btnCaptureSearchArea)
        val btnToggleShape = view.findViewById<Button>(R.id.btnToggleCaptureShape)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        val dm = service.resources.displayMetrics
        val screenW = dm.widthPixels
        val screenH = dm.heightPixels

        var frameW = overlayManager.dpToPx(100)
        var frameH = overlayManager.dpToPx(100)
        var frameX = (screenW - frameW) / 2
        var frameY = (screenH - frameH) / 2

        fun updatePositions() {
            frameW = frameW.coerceIn(overlayManager.dpToPx(24), screenW)
            frameH = frameH.coerceIn(overlayManager.dpToPx(24), screenH)
            frameX = frameX.coerceIn(0, screenW - frameW)
            frameY = frameY.coerceIn(0, screenH - frameH)

            captureSquare?.apply {
                layoutParams?.width = frameW
                layoutParams?.height = frameH
                translationX = frameX.toFloat()
                translationY = frameY.toFloat()
                requestLayout()
            }

            layoutTopBar?.apply {
                translationX = frameX.toFloat().coerceIn(0f, (screenW - width).toFloat().coerceAtLeast(0f))
                translationY = (frameY - overlayManager.dpToPx(44)).toFloat().coerceIn(0f, (screenH - height).toFloat().coerceAtLeast(0f))
            }

            layoutBottomBar?.apply {
                translationX = frameX.toFloat().coerceIn(0f, (screenW - width).toFloat().coerceAtLeast(0f))
                translationY = (frameY + frameH + overlayManager.dpToPx(4)).toFloat().coerceIn(0f, (screenH - height).toFloat().coerceAtLeast(0f))
            }
        }

        var initFrameX = 0
        var initFrameY = 0
        var touchX = 0f
        var touchY = 0f

        handleMove?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initFrameX = frameX
                    initFrameY = frameY
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    frameX = initFrameX + (event.rawX - touchX).toInt()
                    frameY = initFrameY + (event.rawY - touchY).toInt()
                    updatePositions()
                    true
                }
                else -> false
            }
        }

        var initW = 0
        var initH = 0
        handleResize?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initW = frameW
                    initH = frameH
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    frameW = initW + (event.rawX - touchX).toInt()
                    frameH = initH + (event.rawY - touchY).toInt()
                    updatePositions()
                    true
                }
                else -> false
            }
        }

        var isCircle = true
        btnToggleShape?.setOnClickListener {
            service.vibrateFeedback(20L)
            isCircle = !isCircle
            btnToggleShape.text = if (isCircle) "🔘" else "🔲"
            captureSquare?.setBackgroundResource(
                if (isCircle) R.drawable.border_capture else R.drawable.border_capture_square
            )
        }

        btnSearchArea?.setOnClickListener {
            service.vibrateFeedback(20L)
            Toast.makeText(service, "📐 Зона поиска задана", Toast.LENGTH_SHORT).show()
        }

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(40L)
            hide()
            service.addNewActionAtPosition(
                frameX + frameW / 2f,
                frameY + frameH / 2f,
                1000L,
                ActionType.TRIGGER,
                -1
            )
            Toast.makeText(service, "🎉 ИИ-Шаблон добавлен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        view.post { updatePositions() }
    }

    fun capture(): Bitmap? {
        return try {
            val dm = service.resources.displayMetrics
            Bitmap.createBitmap(dm.widthPixels, dm.heightPixels, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
