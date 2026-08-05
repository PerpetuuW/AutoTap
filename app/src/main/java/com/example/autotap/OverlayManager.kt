package com.example.autotap

import com.example.autotap.*

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView

class OverlayManager(private val context: Context) {

    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private val activeTargetViews = mutableListOf<View>()

    private fun createBaseLayoutParams(x: Int, y: Int): WindowManager.LayoutParams {
        return WindowManager.LayoutParams().apply {
            type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
            
            this.gravity = Gravity.TOP or Gravity.START
            this.x = x
            this.y = y
            this.width = 48.dpToPx(context)
            this.height = 48.dpToPx(context)
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    fun spawnEndTargetAtPosition(x: Int, y: Int, targetNumber: Int): View {
        val layoutParams = createBaseLayoutParams(x, y)

        val targetContainer = FrameLayout(context).apply {
            setBackgroundColor(Color.argb(180, 255, 87, 34))
        }

        val label = TextView(context).apply {
            text = "E$targetNumber"
            setTextColor(Color.WHITE)
            textSize = 12f
            gravity = Gravity.CENTER
        }
        targetContainer.addView(label)

        targetContainer.setOnTouchListener(object : View.OnTouchListener {
            private var initialX = 0
            private var initialY = 0
            private var touchX = 0f
            private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = layoutParams.x
                        initialY = layoutParams.y
                        touchX = event.rawX
                        touchY = event.rawY
                        context.vibrateFeedback(30L)
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        layoutParams.x = initialX + (event.rawX - touchX).toInt()
                        layoutParams.y = initialY + (event.rawY - touchY).toInt()
                        windowManager.updateViewLayout(targetContainer, layoutParams)
                        return true
                    }
                }
                return false
            }
        })

        windowManager.addView(targetContainer, layoutParams)
        activeTargetViews.add(targetContainer)
        DiagnosticLogger.log("OverlayManager", "Spawned target E$targetNumber at ($x, $y)")
        return targetContainer
    }

    fun removeAllTargets() {
        for (view in activeTargetViews) {
            try {
                windowManager.removeView(view)
            } catch (e: Exception) {
                DiagnosticLogger.log("OverlayManager", "Error removing view: ${e.message}")
            }
        }
        activeTargetViews.clear()
    }
}
