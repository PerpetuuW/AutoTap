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
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_control_panel, OverlayLayer.PANEL, OverlayPriority.MEDIUM) {

    private var stopButtonView: View? = null
    private var panelState = 0

    private var btnPlay: ImageButton? = null
    private var btnAdd: ImageButton? = null
    private var btnCapturePool: ImageButton? = null
    private var btnHelpTutorial: ImageButton? = null
    private var btnToggleMenu: ImageButton? = null

    private var btnClearAll: ImageButton? = null
    private var btnRecord: ImageButton? = null
    private var btnToggleJoystick: ImageButton? = null
    private var btnLoadScript: ImageButton? = null
    private var btnHideNumbers: ImageButton? = null
    private var btnClose: ImageButton? = null
    private var btnSingleBubble: ImageButton? = null

    private var layoutMainRow: View? = null
    private var layoutSubMenu: View? = null

    override fun onViewInflated(view: View) {
        val handleDrag = view.findViewById<TextView>(R.id.handleDrag)
        layoutMainRow = view.findViewById(R.id.layoutMainRow)
        layoutSubMenu = view.findViewById(R.id.layoutSubMenu)
        btnSingleBubble = view.findViewById(R.id.btnSingleBubble)

        btnPlay = view.findViewById(R.id.btnPlay)
        btnAdd = view.findViewById(R.id.btnAdd)
        btnCapturePool = view.findViewById(R.id.btnCapturePool)
        btnHelpTutorial = view.findViewById(R.id.btnHelpTutorial)
        btnToggleMenu = view.findViewById(R.id.btnToggleMenu)

        btnClearAll = view.findViewById(R.id.btnClearAll)
        btnRecord = view.findViewById(R.id.btnRecord)
        btnToggleJoystick = view.findViewById(R.id.btnToggleJoystick)
        btnLoadScript = view.findViewById(R.id.btnLoadScript)
        btnHideNumbers = view.findViewById(R.id.btnHideNumbers)
        btnClose = view.findViewById(R.id.btnClose)

        var initX = 0; var initY = 0; var touchX = 0f; var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val p = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x
                    initY = p.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (screenW, screenH) = service.overlayManager.getRealScreenSize()
                    val w = if (view.width > 0) view.width else service.dpToPx(180)
                    val h = if (view.height > 0) view.height else service.dpToPx(50)
                    val maxX = (screenW - w).coerceAtLeast(0)
                    val maxY = (screenH - h).coerceAtLeast(0)
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxY)
                    service.overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        btnToggleMenu?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(panelState + 1) }
        btnSingleBubble?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(0) }

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (service.isPlaying) {
                btnPlay?.setImageResource(R.drawable.ic_play)
                service.stopExecutionLoop()
            } else {
                btnPlay?.setImageResource(R.drawable.ic_pause)
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

    fun ensureSubMenuVisible() {
        if (panelState != 1) {
            updatePanelState(1)
        }
    }

    fun getButtonForStep(step: Int): View? {
        return when (step) {
            0 -> btnPlay
            1 -> btnAdd
            2 -> btnCapturePool
            3 -> btnHelpTutorial
            4 -> btnToggleMenu
            5 -> btnClearAll
            6 -> btnRecord
            7 -> btnToggleJoystick
            8 -> btnLoadScript
            9 -> btnHideNumbers
            10 -> btnClose
            else -> null
        }
    }

    fun resetAllButtonScales() {
        val buttons = listOf(
            btnPlay, btnAdd, btnCapturePool, btnHelpTutorial, btnToggleMenu,
            btnClearAll, btnRecord, btnToggleJoystick, btnLoadScript, btnHideNumbers, btnClose
        )
        buttons.forEach { btn ->
            btn?.scaleX = 1.0f
            btn?.scaleY = 1.0f
        }
    }

    fun updatePanelState(state: Int) {
        panelState = state % 3
        when (panelState) {
            0 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.GONE }
            1 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.VISIBLE; btnSingleBubble?.visibility = View.GONE }
            2 -> { layoutMainRow?.visibility = View.GONE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.VISIBLE }
        }
        rootView?.requestLayout()
        val p = rootView?.layoutParams as? WindowManager.LayoutParams
        if (p != null && rootView != null) {
            p.width = WindowManager.LayoutParams.WRAP_CONTENT
            p.height = WindowManager.LayoutParams.WRAP_CONTENT
            service.overlayManager.safeUpdateViewLayout(rootView, p)
        }
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
