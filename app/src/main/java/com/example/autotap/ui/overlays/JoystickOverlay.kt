package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.PointF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import kotlin.math.hypot
import kotlin.math.min

class JoystickOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_joystick_control, OverlayLayer.JOYSTICK, OverlayPriority.HIGH) {

    private var handleMove: View? = null
    private var btnRecord: Button? = null
    private var btnClose: ImageButton? = null
    private var touchArea: View? = null
    private var viewKnob: View? = null

    private val rawPoints = ArrayList<PointF>()
    private val smoothedPoints = ArrayList<PointF>()
    private var isRecordingPath = false
    private var joystickStartTime = 0L

    override fun onViewInflated(view: View) {
        handleMove = view.findViewById(R.id.handleMoveJoystick)
        btnRecord = view.findViewById(R.id.btnRecordJoystick)
        btnClose = view.findViewById(R.id.btnCloseJoystick)
        touchArea = view.findViewById(R.id.viewJoystickBase)
        viewKnob = view.findViewById(R.id.viewJoystickKnob)

        bindInteractions()
    }

    override fun createParams(): WindowManager.LayoutParams {
        val sizePx = service.dpToPx(160)
        return service.overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx + service.dpToPx(40)
            gravity = Gravity.TOP or Gravity.START
            x = service.dpToPx(30)
            y = service.dpToPx(240)
        }
    }

    private fun bindInteractions() {
        var initX = 0; var initY = 0
        var touchX = 0f; var touchY = 0f

        handleMove?.setOnTouchListener { _, event ->
            val p = rootView?.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x; initY = p.y
                    touchX = event.rawX; touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (screenW, screenH) = service.overlayManager.getRealScreenSize()
                    val sizePx = service.dpToPx(160)
                    p.gravity = Gravity.TOP or Gravity.START
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (screenW - sizePx).coerceAtLeast(0))
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(service.dpToPx(60), (screenH - sizePx).coerceAtLeast(service.dpToPx(60)))
                    service.overlayManager.safeUpdateViewLayout(rootView, p)
                    true
                }
                else -> false
            }
        }

        var startX = 0f; var startY = 0f
        val maxRadiusPx = service.dpToPx(50).toFloat()

        viewKnob?.setOnTouchListener(object : View.OnTouchListener {
            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        startX = event.rawX; startY = event.rawY
                        joystickStartTime = System.currentTimeMillis()
                        rawPoints.clear()
                        rawPoints.add(PointF(startX, startY))
                        service.vibrateFeedback(20L)
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = event.rawX - startX
                        val dy = event.rawY - startY
                        val dist = hypot(dx.toDouble(), dy.toDouble()).toFloat()
                        val angle = Math.atan2(dy.toDouble(), dx.toDouble())
                        val clampedDist = min(dist, maxRadiusPx)

                        val knobX = (clampedDist * Math.cos(angle)).toFloat()
                        val knobY = (clampedDist * Math.sin(angle)).toFloat()

                        viewKnob?.translationX = knobX
                        viewKnob?.translationY = knobY

                        if (isRecordingPath) {
                            val pt = PointF(startX + knobX, startY + knobY)
                            val last = rawPoints.lastOrNull()
                            if (last == null || hypot((pt.x - last.x).toDouble(), (pt.y - last.y).toDouble()) > 3.0) {
                                rawPoints.add(pt)
                            }
                        }
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        val duration = (System.currentTimeMillis() - joystickStartTime).coerceIn(100L, 5000L)
                        val finalDx = viewKnob?.translationX ?: 0f
                        val finalDy = viewKnob?.translationY ?: 0f
                        val finalDist = hypot(finalDx.toDouble(), finalDy.toDouble()).toFloat()

                        viewKnob?.animate()?.translationX(0f)?.translationY(0f)?.setDuration(180)?.start()

                        if (finalDist > 15) {
                            val params = rootView?.layoutParams as? WindowManager.LayoutParams
                            val sizePx = service.dpToPx(160)
                            val centerX = (params?.x ?: 0) + sizePx / 2f
                            val centerY = (params?.y ?: 0) + service.dpToPx(30) + sizePx / 2f
                            val targetX = centerX + finalDx
                            val targetY = centerY + finalDy

                            smoothPathTrajectory()
                            service.performSwipeWithCallback(centerX, centerY, targetX, targetY, duration)

                            if (isRecordingPath) {
                                val normPath = ArrayList<PointF>().apply {
                                    smoothedPoints.forEach { p ->
                                        add(PointF(service.normalizeX(p.x), service.normalizeY(p.y)))
                                    }
                                }
                                val first = normPath.firstOrNull() ?: PointF(service.normalizeX(centerX), service.normalizeY(centerY))
                                val last = normPath.lastOrNull() ?: PointF(service.normalizeX(targetX), service.normalizeY(targetY))

                                val cfg = ActionConfig(
                                    id = service.actionsList.size + 1,
                                    type = ActionType.SWIPE_PATH,
                                    xNorm = first.x,
                                    yNorm = first.y,
                                    endXNorm = last.x,
                                    endYNorm = last.y,
                                    holdDuration = duration,
                                    joystickPath = normPath
                                )

                                service.actionsList.add(cfg)
                                service.spawnEndTargetAtPosition(cfg, targetX, targetY)
                                Toast.makeText(service, "🕹 Записано движение джойстика (${duration}мс)!", Toast.LENGTH_SHORT).show()
                            }
                        }
                        return true
                    }
                }
                return false
            }
        })

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(25L)
            isRecordingPath = !isRecordingPath
            btnRecord?.text = if (isRecordingPath) "🔴 Запись..." else "⏺ ЗАПИСАТЬ"
            btnRecord?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isRecordingPath) R.color.red_close else R.color.accent_blue))
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }
    }

    private fun smoothPathTrajectory() {
        smoothedPoints.clear()
        if (rawPoints.size < 3) {
            smoothedPoints.addAll(rawPoints)
            return
        }

        smoothedPoints.add(rawPoints.first())
        for (i in 1 until rawPoints.size - 1) {
            val prev = rawPoints[i - 1]
            val curr = rawPoints[i]
            val next = rawPoints[i + 1]

            val smX = (prev.x + curr.x + next.x) / 3f
            val smY = (prev.y + curr.y + next.y) / 3f
            smoothedPoints.add(PointF(smX, smY))
        }
        smoothedPoints.add(rawPoints.last())
    }
}
