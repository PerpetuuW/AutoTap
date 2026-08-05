package com.example.autotap

import android.content.Context
import android.graphics.Point
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager

// 1. Расширения конвертации dp в px
fun Int.dpToPx(context: Context): Int {
    return (this * context.resources.displayMetrics.density).toInt()
}

fun Float.dpToPx(context: Context): Float {
    return this * context.resources.displayMetrics.density
}

// 2. Деструктуризация для класса Point (убирает ошибки component1() / component2())
operator fun Point.component1(): Int = this.x
operator fun Point.component2(): Int = this.y

// 3. Нормализация координат под физические границы экрана
fun Context.normalizeX(x: Int, screenWidth: Int): Int {
    return x.coerceIn(0, screenWidth)
}

fun Context.normalizeY(y: Int, screenHeight: Int): Int {
    return y.coerceIn(0, screenHeight)
}

// 4. Полноценная поддержка виброотклика (vibrateFeedback) без заглушек
fun Context.vibrateFeedback(durationMs: Long = 50L) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VibratorManagerService) as VibratorManager
            val vibrator = vibratorManager.defaultVibrator
            vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(durationMs)
            }
        }
    } catch (e: Exception) {
        DiagnosticLogger.log("VibrateFeedback", "Vibration failure: ${e.message}")
    }
}