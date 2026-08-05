package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.PixelFormat
import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import android.view.ContextThemeWrapper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.Toast
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import kotlin.math.hypot
import kotlin.math.min

class JoystickOverlay(private val service: MyAutoClickService) {

    var joystickOverlayView: View? = null

    fun show() {
        if (joystickOverlayView != null) {
            joystickOverlayView?.visibility = View.VISIBLE
            return
        }

        val contextThemeWrapper = ContextThemeWrapper(service, R.style.Theme_AutoTap)
        joystickOverlayView = LayoutInflater.from(contextThemeWrapper)
            .inflate(R.layout.floating_joystick_control, null)

        val displayMetrics = service.resources.displayMetrics
        val screenW = displayMetrics.widthPixels
        val screenH = displayMetrics.heightPixels

        val sizePx = service.overlayManager.dpToPx(160)
        val params = WindowManager.LayoutParams(
            sizePx,
            sizePx + service.overlayManager.dpToPx(40),
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = service.overlayManager.dpToPx(30)
            y = screenH / 2 - sizePx / 2
        }

        val handleMove = joystickOverlayView!!.findViewById<View>(R.id.handleMoveJoystick)
        val btnClose = joystickOverlayView!!.findViewById<View>(R.id.btnCloseJoystick)
        val btnRecordJoystick = joystickOverlayView!!.findViewById<Button>(R.id.btnRecordJoystick)
        val viewKnob = joystickOverlayView!!.findViewById<View>(R.id.viewJoystickKnob)

        var isJoystickRecording = false
        var joystickStartTime = 0L
        var startTouchX = 0f
        var startTouchY = 0f
        var isJoystickHeld = false
        var currentDx = 0f
        var currentDy = 0f

        val currentPathPoints = ArrayList<PointF>()

        val dragFrameListener = object : View.OnTouchListener {
            private var initX = 0; private var initY = 0
            private var touchX = 0f; private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, screenW - sizePx)
                        params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, screenH - sizePx)
                        service.overlayManager.safeUpdateViewLayout(joystickOverlayView, params)
                        return true
                    }
                }
                return false
            }
        }
        handleMove?.setOnTouchListener(dragFrameListener)

        viewKnob?.setOnTouchListener(object : View.OnTouchListener {
            private val maxRadiusPx = service.overlayManager.dpToPx(50).toFloat()

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        startTouchX = event.rawX
                        startTouchY = event.rawY
                        joystickStartTime = System.currentTimeMillis()
                        isJoystickHeld = true
                        service.vibrateFeedback(20L)

                        val baseX = params.x + sizePx / 2f
                        val baseY = params.y + service.overlayManager.dpToPx(30) + sizePx / 2f
                        currentPathPoints.clear()
                        currentPathPoints.add(PointF(baseX, baseY))
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        if (!isJoystickHeld) return false
                        val dx = event.rawX - startTouchX
                        val dy = event.rawY - startTouchY
                        val dist = hypot(dx.toDouble(), dy.toDouble()).toFloat()

                        val angle = Math.atan2(dy.toDouble(), dx.toDouble())
                        val clampedDist = min(dist, maxRadiusPx)

                        currentDx = (clampedDist * Math.cos(angle)).toFloat()
                        currentDy = (clampedDist * Math.sin(angle)).toFloat()

                        viewKnob.translationX = currentDx
                        viewKnob.translationY = currentDy

                        val baseX = params.x + sizePx / 2f
                        val baseY = params.y + service.overlayManager.dpToPx(30) + sizePx / 2f
                        val px = (baseX + currentDx * 3.5f).coerceIn(0f, screenW.toFloat())
val py = (baseY + currentDy * 3.5f).coerceIn(0f, screenH.toFloat())

// Anti‑jitter: добавляем точку только при значимом движении
if (currentPathPoints.isEmpty() ||
    hypot((px - currentPathPoints.last().x).toDouble(),
          (py - currentPathPoints.last().y).toDouble()) > 3.0) {
    currentPathPoints.add(PointF(px, py))
}
                        return true
                    }

                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        v.performClick()
                        isJoystickHeld = false

                        val duration = (System.currentTimeMillis() - joystickStartTime).coerceIn(150L, 60000L)
                        val finalDx = viewKnob.translationX
                        val finalDy = viewKnob.translationY
                        val finalDist = hypot(finalDx.toDouble(), finalDy.toDouble()).toFloat()

                        viewKnob.animate().translationX(0f).translationY(0f).setDuration(180).start()

                        if (finalDist > 10) {
                            val baseX = params.x + sizePx / 2f
                            val baseY = params.y + service.overlayManager.dpToPx(30) + sizePx / 2f
                            val targetX = (baseX + finalDx * 3.5f).coerceIn(0f, screenW.toFloat())
                            val targetY = (baseY + finalDy * 3.5f).coerceIn(0f, screenH.toFloat())

                            if (isJoystickRecording) {
                                service.addNewActionAtPosition(baseX, baseY, 500L, ActionType.JOYSTICK_PATH, -1)
                                val cfg = service.actionsList.last()
                                cfg.holdDuration = duration
                                cfg.joystickPath = ArrayList(currentPathPoints)
                                service.spawnEndTargetAtPosition(cfg, targetX, targetY)

                                Toast.makeText(
                                    service,
                                    "🕹 Записана траектория джойстика (${duration}мс)!",
                                    Toast.LENGTH_SHORT
                                ).show()
                            }

                            joystickOverlayView?.visibility = View.INVISIBLE
                            Handler(Looper.getMainLooper()).postDelayed({
                                service.gestureExecutor.performPathSwipeWithCallback(
                                    currentPathPoints, baseX, baseY, targetX, targetY, duration
                                ) {
                                    Handler(Looper.getMainLooper()).post {
                                        joystickOverlayView?.visibility = View.VISIBLE
                                    }
                                }
                            }, 50L)
                        }
                        currentDx = 0f; currentDy = 0f
                        return true
                    }
                }
                return false
            }
        })

        btnRecordJoystick?.setOnClickListener {
            service.vibrateFeedback(25L)
            isJoystickRecording = !isJoystickRecording
            btnRecordJoystick.text = if (isJoystickRecording) "🔴 Запись..." else "⏺ ЗАПИСАТЬ"
            btnRecordJoystick.backgroundTintList =
                ColorStateList.valueOf(service.getColor(if (isJoystickRecording) R.color.red_close else R.color.accent_blue))

            if (isJoystickRecording) {
                service.isRecording = true
                service.actionsList.forEach { act ->
                    act.startView.visibility = View.INVISIBLE
                    act.endView?.visibility = View.INVISIBLE
                }
                service.controlPanelView?.visibility = View.GONE
                service.showFloatingStopButton()
            } else {
                service.stopOverlayRecording()
            }
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(25L)
            hide()
        }

        service.overlayManager.safeAddView(joystickOverlayView, params)
    }

    fun hide() {
        if (joystickOverlayView != null) {
            service.overlayManager.safeRemoveView(joystickOverlayView)
            joystickOverlayView = null
        }
    }
}
