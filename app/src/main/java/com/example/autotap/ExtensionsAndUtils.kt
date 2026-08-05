package com.example.autotap

import com.example.autotap.*

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.Gravity
import android.view.View
import android.view.WindowManager

fun logAppEvent(event: String, details: String = "") {
    DiagnosticLogger.log("AppEvent", event, mapOf("details" to details))
}

fun logError(tag: String, message: String, throwable: Throwable? = null) {
    DiagnosticLogger.log(tag, "ERROR: $message | ${throwable?.message ?: ""}")
}

fun Int.dpToPx(context: Context): Int = (this * context.resources.displayMetrics.density).toInt()
fun Float.dpToPx(context: Context): Float = this * context.resources.displayMetrics.density

operator fun Point.component1(): Int = this.x
operator fun Point.component2(): Int = this.y
val Point.first: Int get() = this.x
val Point.second: Int get() = this.y

fun resolveNormalizedPoint(x: Int, y: Int, screenWidth: Int, screenHeight: Int): Point {
    return Point(x.coerceIn(0, screenWidth), y.coerceIn(0, screenHeight))
}

fun Context.getRealScreenSize(): Point {
    val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
    val display = wm.defaultDisplay
    val size = Point()
    display.getRealSize(size)
    return size
}

fun Context.normalizeX(x: Int, screenWidth: Int): Int = x.coerceIn(0, screenWidth)
fun Context.normalizeY(y: Int, screenHeight: Int): Int = y.coerceIn(0, screenHeight)

fun Context.vibrateFeedback(durationMs: Long = 50L) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            val vibrator = vibratorManager?.defaultVibrator
            vibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                vibrator?.vibrate(durationMs)
            }
        }
    } catch (e: Exception) {
        DiagnosticLogger.log("VibrateFeedback", "Vibration failed: ${e.message}")
    }
}

fun WindowManager.createOverlayParams(widthPx: Int = WindowManager.LayoutParams.WRAP_CONTENT, heightPx: Int = WindowManager.LayoutParams.WRAP_CONTENT): WindowManager.LayoutParams {
    return WindowManager.LayoutParams().apply {
        type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        format = PixelFormat.TRANSLUCENT
        flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        }
        gravity = Gravity.TOP or Gravity.START
        width = widthPx
        height = heightPx
    }
}

fun WindowManager.safeAddView(view: View, params: WindowManager.LayoutParams) {
    try {
        if (view.parent == null) {
            addView(view, params)
        }
    } catch (e: Exception) {
        logError("WindowManager", "safeAddView failed: ${e.message}")
    }
}

fun WindowManager.safeRemoveView(view: View?) {
    if (view == null) return
    try {
        if (view.parent != null) {
            removeView(view)
        }
    } catch (e: Exception) {
        logError("WindowManager", "safeRemoveView failed: ${e.message}")
    }
}

fun WindowManager.safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
    if (view == null) return
    try {
        if (view.parent != null) {
            updateViewLayout(view, params)
        }
    } catch (e: Exception) {
        logError("WindowManager", "safeUpdateViewLayout failed: ${e.message}")
    }
}

fun getViewFromReusePool(context: Context): View? = null
fun recycleViewToPool(view: View?) {}
