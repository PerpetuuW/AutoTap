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
    val overlayManager: OverlayManager = service.overlayManager
) {

    var rootView: View? = null
    private val pathPoints = ArrayList<PointF>()
    private var isRecordingPath = false

    fun show() {
        if (rootView != null) return

        val view = View.inflate(service, R.layout.floating_joystick_control, null)
        rootView = view

        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = overlayManager.dpToPx(30)
            y = overlayManager.dpToPx(200)
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
        val handleMove = view.findViewById<View>(R.id.handleMoveJoystick)
        val btnRecord = view.findViewById<Button>(R.id.btnRecordJoystick)
        val btnClose = view.findViewById<ImageButton>(R.id.btnCloseJoystick)
        val touchArea = view.findViewById<View>(R.id.viewJoystickBase)

        var initX = 0
        var initY = 0
        var touchX = 0f
        var touchY = 0f

        handleMove?.setOnTouchListener { _, event ->
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
                    val dm = service.resources.displayMetrics
                    val maxX = dm.widthPixels - view.width
                    val maxY = dm.heightPixels - view.height
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxX)
                    overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

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
