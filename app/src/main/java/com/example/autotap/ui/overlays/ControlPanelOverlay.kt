package com.example.autotap.ui.overlays

import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ControlPanelOverlay(private val service: MyAutoClickService) {

    private var panelView: View? = null
    private var stopButtonView: View? = null
    private var panelState = 0

    fun show() {
        if (panelView != null) {
            panelView?.visibility = View.VISIBLE
            return
        }

        val view = LayoutInflater.from(service).inflate(R.layout.floating_control_panel, null)
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
        panelView?.let { service.overlayManager.safeRemoveView(it) }
        panelView = null
    }

    private fun bindUi(view: View) {
        val handleDrag = view.findViewById<TextView>(R.id.handleDrag)
        val layoutMainRow = view.findViewById<View>(R.id.layoutMainRow)
        val layoutSubMenu = view.findViewById<View>(R.id.layoutSubMenu)
        val btnSingleBubble = view.findViewById<ImageButton>(R.id.btnSingleBubble)

        val btnPlay = view.findViewById<ImageButton>(R.id.btnPlay)
        val btnAdd = view.findViewById<ImageButton>(R.id.btnAdd)
        val btnCapturePool = view.findViewById<ImageButton>(R.id.btnCapturePool)
        val btnHelpTutorial = view.findViewById<ImageButton>(R.id.btnHelpTutorial)
        val btnToggleMenu = view.findViewById<ImageButton>(R.id.btnToggleMenu)

        val btnClearAll = view.findViewById<ImageButton>(R.id.btnClearAll)
        val btnRecord = view.findViewById<ImageButton>(R.id.btnRecord)
        val btnToggleJoystick = view.findViewById<ImageButton>(R.id.btnToggleJoystick)
        val btnLoadScript = view.findViewById<ImageButton>(R.id.btnLoadScript)
        val btnHideNumbers = view.findViewById<ImageButton>(R.id.btnHideNumbers)
        val btnClose = view.findViewById<ImageButton>(R.id.btnClose)

        var initX = 0; var initY = 0; var touchX = 0f; var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val params = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = params.x; initY = params.y
                    touchX = event.rawX; touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (screenW, screenH) = service.overlayManager.getRealScreenSize()
                    val w = if (view.width > 0) view.width else service.overlayManager.dpToPx(180)
                    val h = if (view.height > 0) view.height else service.overlayManager.dpToPx(50)
                    params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (screenW - w).coerceAtLeast(0))
                    params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (screenH - h).coerceAtLeast(0))
                    service.overlayManager.safeUpdateViewLayout(view, params)
                    true
                }
                else -> false
            }
        }

        fun updatePanelState(state: Int) {
            panelState = state % 3
            when (panelState) {
                0 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.GONE }
                1 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.VISIBLE; btnSingleBubble?.visibility = View.GONE }
                2 -> { layoutMainRow?.visibility = View.GONE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.VISIBLE }
            }
            view.requestLayout()
            val p = view.layoutParams as? WindowManager.LayoutParams
            if (p != null) {
                p.width = WindowManager.LayoutParams.WRAP_CONTENT
                p.height = WindowManager.LayoutParams.WRAP_CONTENT
                service.overlayManager.safeUpdateViewLayout(view, p)
            }
        }

        btnToggleMenu?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(panelState + 1) }
        btnSingleBubble?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(0) }

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (service.isPlaying) {
                btnPlay.setImageResource(R.drawable.ic_play)
                service.stopExecutionLoop()
            } else {
                btnPlay.setImageResource(R.drawable.ic_pause)
                service.startScript("default")
            }
        }

        btnAdd?.setOnClickListener { service.vibrateFeedback(20L); service.showAddActionMenu() }
        btnCapturePool?.setOnClickListener { service.vibrateFeedback(20L); service.captureFrameOverlay.show() }
        btnHelpTutorial?.setOnClickListener { service.vibrateFeedback(20L); service.showTutorialCard() }
        btnClearAll?.setOnClickListener { service.vibrateFeedback(30L); service.clearAllActions() }
        btnRecord?.setOnClickListener { service.vibrateFeedback(20L); if (service.isRecording) service.stopOverlayRecording() else service.startOverlayRecording() }
        btnToggleJoystick?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.joystickOverlay.rootView != null) service.joystickOverlay.hide() else service.joystickOverlay.show()
        }
        btnLoadScript?.setOnClickListener { service.vibrateFeedback(20L); service.showScriptsDialog() }
        btnHideNumbers?.setOnClickListener { service.vibrateFeedback(20L); service.toggleNumbersVisibility() }
        btnClose?.setOnClickListener { service.vibrateFeedback(20L); service.hideControlPanel(openMainApp = true) }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return
        val view = LayoutInflater.from(service).inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = service.overlayManager.createOverlayParams().apply { gravity = Gravity.CENTER }
        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.stopExecutionLoop()
        }
        service.overlayManager.safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let { service.overlayManager.safeRemoveView(it) }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_beacon_ring, null)
        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }
        service.overlayManager.safeAddView(view, params)
        view.animate().alpha(0f).setDuration(300).withEndAction { service.overlayManager.safeRemoveView(view) }.start()
    }
}
