package com.example.autotap.ui.overlays

import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class CaptureFrameOverlay(
    private val service: MyAutoClickService,
    private val overlayManager: OverlayManager = service.overlayManager
) {

    private var rootView: View? = null

    fun show() {
        hide()

        val view = LayoutInflater.from(service)
            .inflate(R.layout.floating_capture_frame, null)

        rootView = view

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(30L)
            hide()
        }

        btnCancel?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }

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

    fun capture(): Bitmap? {
        return try {
            val dm = service.resources.displayMetrics
            val width = dm.widthPixels
            val height = dm.heightPixels
            Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
