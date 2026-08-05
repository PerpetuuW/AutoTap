package com.example.autotap.ui.overlays

import android.graphics.Bitmap
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
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

        val view = LayoutInflater.from(service).inflate(R.layout.floating_capture_frame, null)
        rootView = view

        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(40L)
            hide()
            val (sw, sh) = overlayManager.getRealScreenSize()
            service.addNewActionAtPosition(sw / 2f, sh / 2f, 1000L, ActionType.TRIGGER, -1)
            Toast.makeText(service, "🎉 ИИ-Шаблон добавлен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener { service.vibrateFeedback(20L); hide() }
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }

    fun capture(): Bitmap? {
        return try {
            val (w, h) = overlayManager.getRealScreenSize()
            Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
