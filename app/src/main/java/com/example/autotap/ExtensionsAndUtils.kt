package com.example.autotap

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.logger.StructuredLogger

fun Int.dpToPx(context: Context): Int {
    return (this * context.resources.displayMetrics.density).toInt()
}

fun Float.dpToPx(context: Context): Int {
    return (this * context.resources.displayMetrics.density).toInt()
}

fun Context.dpToPx(dp: Int): Int {
    return (dp * resources.displayMetrics.density).toInt()
}

fun Context.getRealScreenSize(): Point {
    val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
    return wm.getRealScreenSizeCompat()
}

fun WindowManager.getRealScreenSizeCompat(): Point {
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        val bounds = currentWindowMetrics.bounds
        Point(bounds.width(), bounds.height())
    } else {
        val point = Point()
        @Suppress("DEPRECATION")
        defaultDisplay?.getRealSize(point)
        point
    }
}

fun createOverlayParams(
    width: Int = WindowManager.LayoutParams.WRAP_CONTENT,
    height: Int = WindowManager.LayoutParams.WRAP_CONTENT,
    gravity: Int = Gravity.TOP or Gravity.START,
    flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
    x: Int = 100,
    y: Int = 200
): WindowManager.LayoutParams {
    return WindowManager.LayoutParams(
        width, height,
        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
        flags,
        PixelFormat.TRANSLUCENT
    ).apply {
        this.gravity = gravity
        this.x = x
        this.y = y
    }
}

fun WindowManager.safeAddView(view: View, params: WindowManager.LayoutParams): Boolean {
    return try {
        addView(view, params)
        true
    } catch (e: Exception) {
        e.printStackTrace()
        false
    }
}

fun WindowManager.safeRemoveView(view: View): Boolean {
    return try {
        removeView(view)
        true
    } catch (e: Exception) {
        e.printStackTrace()
        false
    }
}

fun Context.vibrateFeedback() {
    try {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            getSystemService(Vibrator::class.java)
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        } ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(30L, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(30L)
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
}

fun logAppEvent(category: String, message: String) {
    StructuredLogger.logDiagnostic(category, message)
}
