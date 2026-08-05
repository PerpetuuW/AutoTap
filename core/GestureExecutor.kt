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
import kotlin.math.hypot

class GestureExecutor(private val service: AccessibilityService) {

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

    private fun isPlayingSafe(): Boolean {
        val inst = MyAutoClickService.instance
        return inst != null && inst.isPlaying
    }

    private fun buildTapGesture(x: Float, y: Float, duration: Long): GestureDescription {
        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration.coerceAtLeast(40L))
        return GestureDescription.Builder().addStroke(stroke).build()
    }

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

        if (!isPlayingSafe()) {
            onComplete?.invoke(false)
            return
        }

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }

        val gesture = buildTapGesture(x, y, duration)

        val res = service.dispatchGesture(
            gesture,
            object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    super.onCompleted(gestureDescription)
                    service.clickVisualizer.showClick(android.graphics.PointF(x, y))
                    onComplete?.invoke(true)
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    super.onCancelled(gestureDescription)
                    onComplete?.invoke(false)
                }
            },
            null
        )

        if (!res) onComplete?.invoke(false)
    }

    private fun buildLinearSwipePath(
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float
    ): Path {
        return Path().apply {
            moveTo(startX, startY)
            lineTo(endX, endY)
        }
    }

    private fun thinAndSmoothPath(points: List<PointF>): List<PointF> {
        if (points.size <= 2) return points

        val result = ArrayList<PointF>()
        result.add(points.first())

        var lastKept = points.first()
        val minStep = 6f

        for (i in 1 until points.size - 1) {
            val p = points[i]
            val dist = hypot((p.x - lastKept.x).toDouble(), (p.y - lastKept.y).toDouble()).toFloat()
            if (dist >= minStep) {
                result.add(p)
                lastKept = p
            }
        }

        result.add(points.last())
        return result
    }

    private fun buildPathSwipe(
        pathPoints: List<PointF>,
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float
    ): Path {
        val effectivePoints = if (pathPoints.size >= 2) {
            thinAndSmoothPath(pathPoints)
        } else {
            emptyList()
        }

        return Path().apply {
            if (effectivePoints.size >= 2) {
                moveTo(effectivePoints.first().x, effectivePoints.first().y)
                for (i in 1 until effectivePoints.size) {
                    lineTo(effectivePoints[i].x, effectivePoints[i].y)
                }
            } else {
                moveTo(startX, startY)
                lineTo(endX, endY)
            }
        }
    }

    private fun buildSwipeGesture(path: Path, duration: Long): GestureDescription {
        val safeDuration = duration.coerceIn(120L, 600L)
        val stroke = GestureDescription.StrokeDescription(path, 0, safeDuration)
        return GestureDescription.Builder().addStroke(stroke).build()
    }

    fun performSwipeWithCallback(
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        duration: Long = 300L,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        performPathSwipeWithCallback(emptyList(), startX, startY, endX, endY, duration, onComplete)
    }

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

        if (!isPlayingSafe()) {
            onComplete?.invoke(false)
            return
        }

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }

        val path = buildPathSwipe(pathPoints, startX, startY, endX, endY)
        val gesture = buildSwipeGesture(path, duration)

        val res = service.dispatchGesture(
            gesture,
            object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    super.onCompleted(gestureDescription)
                    service.clickVisualizer.showClick(android.graphics.PointF(x, y))
                    onComplete?.invoke(true)
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    super.onCancelled(gestureDescription)
                    onComplete?.invoke(false)
                }
            },
            null
        )

        if (!res) onComplete?.invoke(false)
    }
}
