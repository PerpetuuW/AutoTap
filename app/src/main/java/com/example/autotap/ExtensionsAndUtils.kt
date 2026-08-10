package com.example.autotap

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.graphics.PointF
import android.graphics.Rect
import android.graphics.RectF
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import com.example.autotap.logger.StructuredLogger
import kotlin.math.max
import kotlin.math.min

object CoordConverter {
    fun toNormalizedPoint(pt: PointF, widthPx: Int, heightPx: Int): PointF {
        val w = widthPx.coerceAtLeast(1).toFloat()
        val h = heightPx.coerceAtLeast(1).toFloat()
        return PointF((pt.x / w).coerceIn(0f, 1f), (pt.y / h).coerceIn(0f, 1f))
    }

    fun toPxPoint(ptNorm: PointF, widthPx: Int, heightPx: Int): PointF {
        return PointF(ptNorm.x * widthPx, ptNorm.y * heightPx)
    }

    fun toNormalizedRect(rect: Rect, widthPx: Int, heightPx: Int): RectF {
        val w = widthPx.coerceAtLeast(1).toFloat()
        val h = heightPx.coerceAtLeast(1).toFloat()

        // Защита от инверсии граней (left > right или top > bottom)
        val left = min(rect.left, rect.right).toFloat()
        val right = max(rect.left, rect.right).toFloat()
        val top = min(rect.top, rect.bottom).toFloat()
        val bottom = max(rect.top, rect.bottom).toFloat()

        return RectF(
            (left / w).coerceIn(0f, 1f),
            (top / h).coerceIn(0f, 1f),
            (right / w).coerceIn(0f, 1f),
            (bottom / h).coerceIn(0f, 1f)
        )
    }

    fun toPxRect(rectNorm: RectF, widthPx: Int, heightPx: Int): Rect {
        val left = min(rectNorm.left, rectNorm.right)
        val right = max(rectNorm.left, rectNorm.right)
        val top = min(rectNorm.top, rectNorm.bottom)
        val bottom = max(rectNorm.top, rectNorm.bottom)

        return Rect(
            (left * widthPx).toInt(),
            (top * heightPx).toInt(),
            (right * widthPx).toInt(),
            (bottom * heightPx).toInt()
        )
    }
}

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

fun View.findViewByNames(vararg idNames: String): View? {
    for (name in idNames) {
        val id = context.resources.getIdentifier(name, "id", context.packageName)
        if (id != 0) {
            val found = findViewById<View>(id)
            if (found != null) return found
        }
    }
    return null
}

fun View.bindClickByNames(vararg idNames: String, onClick: (View) -> Unit): Boolean {
    val target = findViewByNames(*idNames)
    if (target != null) {
        target.setOnClickListener(onClick)
        return true
    }
    return false
}

fun View.bindClickToFirstClickableChild(onClick: (View) -> Unit) {
    if (this is ViewGroup) {
        for (i in 0 until childCount) {
            val child = getChildAt(i)
            if (child.isClickable || child.id != View.NO_ID) {
                child.setOnClickListener(onClick)
            } else if (child is ViewGroup) {
                child.bindClickToFirstClickableChild(onClick)
            }
        }
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
    val windowType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
    } else {
        @Suppress("DEPRECATION")
        WindowManager.LayoutParams.TYPE_PHONE
    }

    return WindowManager.LayoutParams(
        width, height,
        windowType,
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

fun Context.playNotificationAlert(mode: Int) {
    try {
        if (mode == 1 || mode == 3) {
            vibrateFeedback()
        }
        if (mode == 2 || mode == 3) {
            val toneGen = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 80)
            toneGen.startTone(ToneGenerator.TONE_PROP_BEEP, 200)
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
}

fun logAppEvent(category: String, message: String) {
    StructuredLogger.logDiagnostic(category, message)
}
