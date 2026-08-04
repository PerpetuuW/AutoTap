package com.example.autotap.ui.overlays

import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ControlPanelOverlay(private val service: MyAutoClickService) {

    private var panelView: View? = null
    private var stopButtonView: View? = null

    fun show() {
        if (panelView != null) {
            panelView?.visibility = View.VISIBLE
            return
        }

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_control_panel, null)
        panelView = view

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = service.overlayManager.dpToPx(20)
            y = service.overlayManager.dpToPx(120)
        }

        bindUi(view)
        service.overlayManager.safeAddView(view, params)
    }

    fun hide() {
        panelView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        panelView = null
    }

    private fun bindUi(view: View) {
        val btnPlay = view.findViewById<ImageButton>(R.id.btnPlay)
        val btnAdd = view.findViewById<ImageButton>(R.id.btnAdd)
        val btnRecord = view.findViewById<ImageButton>(R.id.btnRecord)
        val btnLoadScript = view.findViewById<ImageButton>(R.id.btnLoadScript)
        val btnClose = view.findViewById<ImageButton>(R.id.btnClose)

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.startScript("default")
        }

        btnAdd?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.captureFrameOverlay.startRecording()
        }

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.captureFrameOverlay.startRecording()
        }

        btnLoadScript?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showScriptsDialog()
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
        }

        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.stopExecutionLoop()
        }

        service.overlayManager.safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_beacon_ring, null)

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.animate()
            .alpha(0f)
            .setDuration(300)
            .withEndAction {
                service.overlayManager.safeRemoveView(view)
            }
            .start()
    }
}
