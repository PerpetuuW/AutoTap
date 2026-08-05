package com.example.autotap.core

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.graphics.PointF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import com.example.autotap.MyAutoClickService
import java.util.ArrayDeque

class GestureExecutor(private val service: AccessibilityService) {

    private val gestureQueue = ArrayDeque<Runnable>()
    private var isProcessingQueue = false
    private val mainHandler = Handler(Looper.getMainLooper())

    fun vibrateFeedback(durationMs: Long = 25L) {
        try {
            val vibrator = service.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (vibrator != null && vibrator.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (_: Exception) {}
    }

    fun randomOffset(radius: Int): PointF {
        if (radius <= 0) return PointF(0f, 0f)
        val dx = (-radius..radius).random().toFloat()
        val dy = (-radius..radius).random().toFloat()
        return PointF(dx, dy)
    }

    private fun processNextGesture() {
        if (isProcessingQueue || gestureQueue.isEmpty()) return
        isProcessingQueue = true
        val task = gestureQueue.poll()
        task?.run()
    }

    private fun finishGestureTask() {
        isProcessingQueue = false
        mainHandler.postDelayed({ processNextGesture() }, 20L)
    }

    fun performClickWithCallback(x: Float, y: Float, duration: Long = 100L, onComplete: ((Boolean) -> Unit)? = null) {
        gestureQueue.add(Runnable {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                MyAutoClickService.logAppEvent(service, "GESTURE", "❌ Ошибка: API Android < 24 не поддерживает жесты")
                onComplete?.invoke(false)
                finishGestureTask()
                return@Runnable
            }

            MyAutoClickService.logAppEvent(service, "GESTURE", "📤 Отправка клика в ОС: pos=($x, $y) | duration=${duration}ms")

            val path = Path().apply { moveTo(x, y) }
            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            val res = service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "✅ Клик выполнен ОС Android: ($x, $y)")
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "⚠️ Клик отменен ОС Android: ($x, $y)")
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                MyAutoClickService.logAppEvent(service, "GESTURE", "❌ dispatchGesture вернул false для клика ($x, $y)")
                onComplete?.invoke(false)
                finishGestureTask()
            }
        })
        processNextGesture()
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        performPathSwipeWithCallback(emptyList(), startX, startY, endX, endY, duration, onComplete)
    }

    fun performPathSwipeWithCallback(pathPoints: List<PointF>, startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        gestureQueue.add(Runnable {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                onComplete?.invoke(false)
                finishGestureTask()
                return@Runnable
            }

            val smoothed = smoothPath(pathPoints)
            val pointCount = if (smoothed.isNotEmpty()) smoothed.size else 2
            MyAutoClickService.logAppEvent(service, "GESTURE", "📤 Отправка свайпа в ОС: ($startX, $startY) -> ($endX, $endY) | точек=$pointCount | duration=${duration}ms")

            val path = Path().apply {
                if (smoothed.size >= 2) {
                    moveTo(smoothed.first().x, smoothed.first().y)
                    for (i in 1 until smoothed.size) {
                        lineTo(smoothed[i].x, smoothed[i].y)
                    }
                } else {
                    moveTo(startX, startY)
                    lineTo(endX, endY)
                }
            }

            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            val res = service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "✅ Свайп выполнен ОС Android")
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "⚠️ Свайп отменен ОС Android")
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                MyAutoClickService.logAppEvent(service, "GESTURE", "❌ dispatchGesture вернул false для свайпа")
                onComplete?.invoke(false)
                finishGestureTask()
            }
        })
        processNextGesture()
    }

    private fun smoothPath(raw: List<PointF>): List<PointF> {
        if (raw.size < 3) return raw
        val smoothed = ArrayList<PointF>()
        smoothed.add(raw.first())
        for (i in 1 until raw.size - 1) {
            val prev = raw[i - 1]
            val curr = raw[i]
            val next = raw[i + 1]
            val smX = (prev.x + curr.x + next.x) / 3f
            val smY = (prev.y + curr.y + next.y) / 3f
            smoothed.add(PointF(smX, smY))
        }
        smoothed.add(raw.last())
        return smoothed
    }
}
