package com.example.autotap.util

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Build
import android.view.View
import android.view.WindowManager
import com.example.autotap.*

val Int.dpToPx: Int
    get() = (this * android.content.res.Resources.getSystem().displayMetrics.density).toInt()

fun Int.dpToPx(): Int = (this * android.content.res.Resources.getSystem().displayMetrics.density).toInt()

fun Int.dpToPx(context: Context): Int = (this * context.resources.displayMetrics.density).toInt()

fun Context.dpToPx(dp: Int): Int = (dp * this.resources.displayMetrics.density).toInt()

fun Context.getRealScreenSize(): Point {
    val wm = this.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    return wm.getRealScreenSize()
}

val Context.realScreenSize: Point
    get() = this.getRealScreenSize()

fun WindowManager.getRealScreenSize(): Point {
    val point = Point()
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        val bounds = this.currentWindowMetrics.bounds
        point.set(bounds.width(), bounds.height())
    } else {
        @Suppress("DEPRECATION")
        val display = this.defaultDisplay
        @Suppress("DEPRECATION")
        display?.getRealSize(point)
    }
    return point
}

fun Context.createOverlayParams(
    width: Int = WindowManager.LayoutParams.WRAP_CONTENT,
    height: Int = WindowManager.LayoutParams.WRAP_CONTENT
): WindowManager.LayoutParams {
    val params = WindowManager.LayoutParams(
        width,
        height,
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else
            @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_PHONE,
        WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
        PixelFormat.TRANSLUCENT
    )
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
        params.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
    }
    return params
}

fun WindowManager.safeAddView(view: View, params: android.view.ViewGroup.LayoutParams): Boolean {
    return try {
        if (view.parent == null) {
            this.addView(view, params)
            true
        } else false
    } catch (e: Exception) {
        android.util.Log.e("AutoTap", "Failed safeAddView: ${e.message}", e)
        false
    }
}

fun WindowManager.safeRemoveView(view: View): Boolean {
    return try {
        if (view.parent != null) {
            this.removeView(view)
            true
        } else false
    } catch (e: Exception) {
        android.util.Log.e("AutoTap", "Failed safeRemoveView: ${e.message}", e)
        false
    }
}

fun WindowManager.safeUpdateViewLayout(view: View, params: android.view.ViewGroup.LayoutParams): Boolean {
    return try {
        if (view.parent != null) {
            this.updateViewLayout(view, params)
            true
        } else false
    } catch (e: Exception) {
        android.util.Log.e("AutoTap", "Failed safeUpdateViewLayout: ${e.message}", e)
        false
    }
}
