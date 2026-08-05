package com.example.autotap.ui.overlays

import android.graphics.PointF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class JoystickOverlay(
    private val service: MyAutoClickService,
    val overlayManager: OverlayManager = service.overlayManager
) {

    var rootView: View? = null

    fun show() {
        if (rootView != null) return

        val view = View.inflate(service, R.layout.floating_joystick_control, null)
        rootView = view

        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = overlayManager.dpToPx(30)
            y = overlayManager.dpToPx(200)
        }

        val btnClose = view.findViewById<ImageButton>(R.id.btnCloseJoystick)
        btnClose?.setOnClickListener { service.vibrateFeedback(20L); hide() }
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }
}
