package com.example.autotap.core

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Path
import android.graphics.Rect
import android.hardware.HardwareBuffer
import android.os.Build
import android.util.Log
import android.view.Display
import android.accessibilityservice.AccessibilityService.TakeScreenshotCallback
import androidx.annotation.RequiresApi
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CompletableFuture
import com.example.autotap.*

class AutoTapAccessibilityService : AccessibilityService() {

    companion object {
        var instance: AutoTapAccessibilityService? = null
            private set
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        logStructured("AutoTapAccessibilityService connected successfully")
    }

    override fun onAccessibilityEvent(event: android.view.accessibility.AccessibilityEvent?) {}

    override fun onInterrupt() {
        logStructured("AutoTapAccessibilityService interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        if (instance == this) instance = null
        logStructured("AutoTapAccessibilityService destroyed")
    }

    fun performClick(x: Float, y: Float, durationMs: Long = 100L): Boolean {
        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(1L))
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        
        return dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                logStructured("Click dispatched at ($x, $y) for ${durationMs}ms")
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                logStructured("Click CANCELLED at ($x, $y)")
            }
        }, null)
    }

    fun performSwipe(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long = 300L): Boolean {
        val path = Path().apply {
            moveTo(startX, startY)
            lineTo(endX, endY)
        }
        val stroke = GestureDescription.StrokeDescription(path, 0L, durationMs.coerceAtLeast(1L))
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        return dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                logStructured("Swipe dispatched from ($startX, $startY) to ($endX, $endY)")
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                logStructured("Swipe CANCELLED")
            }
        }, null)
    }

    @RequiresApi(Build.VERSION_CODES.R)
    fun captureScreenBitmap(): CompletableFuture<Bitmap?> {
        val future = CompletableFuture<Bitmap?>()
        takeScreenshot(
            Display.DEFAULT_DISPLAY,
            mainExecutor,
            object : TakeScreenshotCallback {
                override fun onSuccess(screenshotResult: ScreenshotResult) {
                    try {
                        val hardwareBuffer: HardwareBuffer = screenshotResult.hardwareBuffer
                        val colorSpace = screenshotResult.colorSpace
                        val bitmap = Bitmap.wrapHardwareBuffer(hardwareBuffer, colorSpace)
                            ?.copy(Bitmap.Config.ARGB_8888, false)
                        hardwareBuffer.close()
                        future.complete(bitmap)
                    } catch (e: Exception) {
                        logStructured("Error converting screenshot HardwareBuffer: ${e.message}")
                        future.complete(null)
                    }
                }

                override fun onFailure(errorCode: Int) {
                    logStructured("takeScreenshot failed with errorCode: $errorCode")
                    future.complete(null)
                }
            }
        )
        return future
    }

    fun samplePixelColor(bitmap: Bitmap, x: Int, y: Int): String {
        val safeX = x.coerceIn(0, bitmap.width - 1)
        val safeY = y.coerceIn(0, bitmap.height - 1)
        val pixel = bitmap.getPixel(safeX, safeY)
        return String.format("#%06X", (0xFFFFFF and pixel))
    }

    fun findColorOnScreen(
        screenBitmap: Bitmap,
        targetColor: Int,
        tolerance: Int,
        searchRegion: Rect
    ): android.graphics.Point? {
        val startX = searchRegion.left.coerceIn(0, screenBitmap.width - 1)
        val startY = searchRegion.top.coerceIn(0, screenBitmap.height - 1)
        val endX = if (searchRegion.right > 0) searchRegion.right.coerceIn(startX, screenBitmap.width) else screenBitmap.width
        val endY = if (searchRegion.bottom > 0) searchRegion.bottom.coerceIn(startY, screenBitmap.height) else screenBitmap.height

        val targetR = Color.red(targetColor)
        val targetG = Color.green(targetColor)
        val targetB = Color.blue(targetColor)

        for (y in startY until endY) {
            for (x in startX until endX) {
                val pixel = screenBitmap.getPixel(x, y)
                val alpha = Color.alpha(pixel)
                if (alpha < 30) continue

                val r = Color.red(pixel)
                val g = Color.green(pixel)
                val b = Color.blue(pixel)

                if (Math.abs(r - targetR) <= tolerance &&
                    Math.abs(g - targetG) <= tolerance &&
                    Math.abs(b - targetB) <= tolerance) {
                    logStructured("Match found at ($x, $y) with color #${Integer.toHexString(pixel)}")
                    return android.graphics.Point(x, y)
                }
            }
        }
        return null
    }

    private fun logStructured(msg: String) {
        val time = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        Log.d("AutoTapService", "[$time] $msg")
    }
}
