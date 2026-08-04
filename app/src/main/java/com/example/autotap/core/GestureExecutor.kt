package com.example.autotap.core

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.graphics.PointF
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import com.example.autotap.MyAutoClickService

class GestureExecutor(private val service: AccessibilityService) {

    // ---------------------------------------------------------
    // ВИБРАЦИЯ
    // ---------------------------------------------------------
    fun vibrateFeedback(durationMs: Long = 25L) {
        try {
            val vibrator = service.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (vibrator != null && vibrator.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(
                        VibrationEffect.createOneShot(
                            durationMs,
                            VibrationEffect.DEFAULT_AMPLITUDE
                        )
                    )
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (_: Exception) {}
    }

    // ---------------------------------------------------------
    // КЛИК С CALLBACK
    // ---------------------------------------------------------
    fun performClickWithCallback(
        x: Float,
        y: Float,
        duration: Long = 100L,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        MyAutoClickService.logAppEvent(
            service,
            "GESTURE",
            "📤 Отправка тапа: ($x, $y), duration=${duration}ms"
        )

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }

        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        val ok = service.dispatchGesture(
            gesture,
            object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(true)
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(false)
                }
            },
            null
        )

        if (!ok) onComplete?.invoke(false)
    }

    // ---------------------------------------------------------
    // SWIPE (прямой)
    // ---------------------------------------------------------
    fun performSwipeWithCallback(
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        duration: Long = 300L,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        performPathSwipeWithCallback(
            emptyList(),
            startX,
            startY,
            endX,
            endY,
            duration,
            onComplete
        )
    }

    // ---------------------------------------------------------
    // SWIPE ПО ТРАЕКТОРИИ
    // ---------------------------------------------------------
    fun performPathSwipeWithCallback(
        pathPoints: List<PointF>,
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        duration: Long = 300L,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        MyAutoClickService.logAppEvent(
            service,
            "GESTURE",
            "📤 Отправка свайпа траектории: points=${pathPoints.size}, duration=${duration}ms"
        )

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }

        val path = Path().apply {
            if (pathPoints.size >= 2) {
                moveTo(pathPoints.first().x, pathPoints.first().y)
                for (i in 1 until pathPoints.size) {
                    lineTo(pathPoints[i].x, pathPoints[i].y)
                }
            } else {
                moveTo(startX, startY)
                lineTo(endX, endY)
            }
        }

        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        val ok = service.dispatchGesture(
            gesture,
            object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(true)
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(false)
                }
            },
            null
        )

        if (!ok) onComplete?.invoke(false)
    }
}
