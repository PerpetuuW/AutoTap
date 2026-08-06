package com.example.autotap.engine

import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.PointF
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import kotlin.random.Random

class GestureExecutor(private val service: MyAutoClickService) {

    fun performClick(x: Float, y: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        try {
            val path = Path()
            path.moveTo(x, y)
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(10L))
            service.dispatchGestureTask(stroke, "Click at ($x, $y)", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения клика ($x, $y)", e)
            callback?.invoke(false)
        }
    }

    fun performClickSync(x: Float, y: Float, durationMs: Long): Boolean {
        performClick(x, y, durationMs, null)
        return true
    }

    fun performClickWithJitter(x: Float, y: Float, jitterRadius: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        val offsetX = if (jitterRadius > 0f) Random.nextFloat() * jitterRadius * 2 - jitterRadius else 0f
        val offsetY = if (jitterRadius > 0f) Random.nextFloat() * jitterRadius * 2 - jitterRadius else 0f
        val targetX = (x + offsetX).coerceAtLeast(0f)
        val targetY = (y + offsetY).coerceAtLeast(0f)
        
        logDiagnostic("GESTURE", "Клик с джиттером: база=($x, $y), итоговая=($targetX, $targetY)")
        performClick(targetX, targetY, durationMs, callback)
    }

    fun performSwipe(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        try {
            val path = Path()
            path.moveTo(startX, startY)
            path.lineTo(endX, endY)
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(100L))
            service.dispatchGestureTask(stroke, "Swipe ($startX, $startY) -> ($endX, $endY)", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения свайпа", e)
            callback?.invoke(false)
        }
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        performSwipe(startX, startY, endX, endY, durationMs, callback)
    }

    fun performLongPress(x: Float, y: Float, holdDurationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        logDiagnostic("GESTURE", "Долгое нажатие ($x, $y) длительность: ${holdDurationMs}мс")
        performClick(x, y, holdDurationMs.coerceAtLeast(500L), callback)
    }

    fun performJoystickPath(pathPoints: List<PointF>, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        if (pathPoints.isEmpty()) {
            logError("GESTURE", "Список точек для джойстика пуст", null)
            callback?.invoke(false)
            return
        }
        try {
            val path = Path()
            path.moveTo(pathPoints[0].x, pathPoints[0].y)
            for (i in 1 until pathPoints.size) {
                path.lineTo(pathPoints[i].x, pathPoints[i].y)
            }
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(200L))
            service.dispatchGestureTask(stroke, "JoystickPath (точек=${pathPoints.size})", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения пути джойстика", e)
            callback?.invoke(false)
        }
    }
}
