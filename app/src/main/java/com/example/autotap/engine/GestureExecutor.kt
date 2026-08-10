package com.example.autotap.engine

import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.PointF
import android.os.Build
import com.example.autotap.MyAutoClickService
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import kotlin.random.Random

class GestureExecutor(private val service: MyAutoClickService) {

    private var activeJoystickStroke: GestureDescription.StrokeDescription? = null
    private var lastJoystickX = 0f
    private var lastJoystickY = 0f

    fun performClick(x: Float, y: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        // КРИТИЧЕСКИЙ ФИКС: Клики сценария не блокируются маркерами мишеней
        try {
            val screenSize = service.getRealScreenSize()
            val safeX = x.coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
            val safeY = y.coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())

            val path = Path()
            path.moveTo(safeX, safeY)
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceIn(10L, 60000L))
            service.dispatchGestureTask(stroke, "Click at ($safeX, $safeY)", callback)
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
        val screenSize = service.getRealScreenSize()
        val offsetX = if (jitterRadius > 0f) Random.nextFloat() * jitterRadius * 2 - jitterRadius else 0f
        val offsetY = if (jitterRadius > 0f) Random.nextFloat() * jitterRadius * 2 - jitterRadius else 0f

        val targetX = (x + offsetX).coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
        val targetY = (y + offsetY).coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())

        performClick(targetX, targetY, durationMs, callback)
    }

    fun performSwipe(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        try {
            val screenSize = service.getRealScreenSize()
            val safeStartX = startX.coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
            val safeStartY = startY.coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())
            val safeEndX = endX.coerceIn(0f, (screenSize.x - 1).coerceAtLeast(1).toFloat())
            val safeEndY = endY.coerceIn(0f, (screenSize.y - 1).coerceAtLeast(1).toFloat())

            val path = Path()
            path.moveTo(safeStartX, safeStartY)
            path.lineTo(safeEndX, safeEndY)
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceIn(50L, 60000L))
            service.dispatchGestureTask(stroke, "Swipe ($safeStartX, $safeStartY) -> ($safeEndX, $safeEndY)", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения свайпа", e)
            callback?.invoke(false)
        }
    }

    fun startContinuousJoystick(centerX: Float, centerY: Float) {
        val screenSize = service.getRealScreenSize()
        val safeX = centerX.coerceIn(0f, (screenSize.x - 1).toFloat())
        val safeY = centerY.coerceIn(0f, (screenSize.y - 1).toFloat())
        lastJoystickX = safeX
        lastJoystickY = safeY

        val path = Path().apply {
            moveTo(safeX, safeY)
            lineTo(safeX, safeY)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val stroke = GestureDescription.StrokeDescription(path, 0L, 100L, true)
            activeJoystickStroke = stroke
            service.dispatchGestureTask(stroke, "StartContinuousJoystick", null)
        }
    }

    fun updateContinuousJoystick(targetX: Float, targetY: Float) {
        val screenSize = service.getRealScreenSize()
        val safeX = targetX.coerceIn(0f, (screenSize.x - 1).toFloat())
        val safeY = targetY.coerceIn(0f, (screenSize.y - 1).toFloat())

        val path = Path().apply {
            moveTo(lastJoystickX, lastJoystickY)
            lineTo(safeX, safeY)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && activeJoystickStroke != null) {
            try {
                val stroke = activeJoystickStroke!!.continueStroke(path, 0L, 80L, true)
                activeJoystickStroke = stroke
                service.dispatchGestureTask(stroke, "UpdateJoystick", null)
            } catch (e: Exception) {
                activeJoystickStroke = null
                startContinuousJoystick(safeX, safeY)
            }
        } else {
            startContinuousJoystick(safeX, safeY)
        }
        lastJoystickX = safeX
        lastJoystickY = safeY
    }

    fun stopContinuousJoystick() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && activeJoystickStroke != null) {
            val path = Path().apply {
                moveTo(lastJoystickX, lastJoystickY)
                lineTo(lastJoystickX, lastJoystickY)
            }
            try {
                val stroke = activeJoystickStroke!!.continueStroke(path, 0L, 50L, false)
                service.dispatchGestureTask(stroke, "StopJoystick", null)
            } catch (_: Exception) {}
            activeJoystickStroke = null
        }
    }

    fun performLongPress(x: Float, y: Float, holdDurationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        performClick(x, y, holdDurationMs.coerceAtLeast(500L), callback)
    }

    fun performJoystickPath(pathPoints: List<PointF>, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        if (pathPoints.isEmpty()) {
            callback?.invoke(false)
            return
        }
        try {
            val screenSize = service.getRealScreenSize()
            val path = Path()
            val firstX = pathPoints[0].x.coerceIn(0f, (screenSize.x - 1).toFloat())
            val firstY = pathPoints[0].y.coerceIn(0f, (screenSize.y - 1).toFloat())
            path.moveTo(firstX, firstY)

            for (i in 1 until pathPoints.size) {
                val px = pathPoints[i].x.coerceIn(0f, (screenSize.x - 1).toFloat())
                val py = pathPoints[i].y.coerceIn(0f, (screenSize.y - 1).toFloat())
                path.lineTo(px, py)
            }
            val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(200L))
            service.dispatchGestureTask(stroke, "JoystickPath (точек=${pathPoints.size})", callback)
        } catch (e: Exception) {
            logError("GESTURE", "Ошибка выполнения пути джойстика", e)
            callback?.invoke(false)
        }
    }
}
