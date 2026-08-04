package com.example.autotap.ui.overlays

import android.graphics.PixelFormat
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
    private val overlayManager: OverlayManager = service.overlayManager
) {

    private var rootView: View? = null
    private val pathPoints = ArrayList<PointF>()
    private var isRecordingPath = false

    fun show() {
        if (rootView != null) return

        val view = View.inflate(service, R.layout.floating_joystick_control, null)
        rootView = view

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

        bindUi(view)
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
        pathPoints.clear()
        isRecordingPath = false
    }

    private fun bindUi(view: View) {
        val btnRecord = view.findViewById<Button>(R.id.btnRecordJoystick)
        val btnClose = view.findViewById<ImageButton>(R.id.btnCloseJoystick)
        val touchArea = view.findViewById<View>(R.id.viewJoystickBase)

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (!isRecordingPath) {
                startRecordingPath()
                btnRecord.text = "⏹ СОХРАНИТЬ"
            } else {
                savePathAsAction()
            }
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        touchArea?.setOnTouchListener { _, event ->
            if (!isRecordingPath) return@setOnTouchListener false

            val x = event.x
            val y = event.y

            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    pathPoints.clear()
                    pathPoints.add(PointF(x, y))
                }
                MotionEvent.ACTION_MOVE -> {
                    pathPoints.add(PointF(x, y))
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    pathPoints.add(PointF(x, y))
                }
            }
            true
        }
    }

    private fun startRecordingPath() {
        pathPoints.clear()
        isRecordingPath = true
    }

    private fun savePathAsAction() {
        if (pathPoints.size < 2) {
            service.vibrateFeedback(40L)
            hide()
            return
        }

        val dm = service.resources.displayMetrics

        val normPath = ArrayList<PointF>().apply {
            pathPoints.forEach { p ->
                add(
                    PointF(
                        (p.x / dm.widthPixels).coerceIn(0f, 1f),
                        (p.y / dm.heightPixels).coerceIn(0f, 1f)
                    )
                )
            }
        }

        val first = normPath.first()
        val last = normPath.last()

        val cfg = ActionConfig(
            id = service.actionsList.size + 1,
            type = ActionType.SWIPE,
            xNorm = first.x,
            yNorm = first.y,
            endXNorm = last.x,
            endYNorm = last.y,
            holdDuration = 600L,
            joystickPath = normPath
        )

        service.actionsList.add(cfg)
        hide()
    }
}
