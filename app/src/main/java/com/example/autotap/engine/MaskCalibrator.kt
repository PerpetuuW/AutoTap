package com.example.autotap.engine

import android.graphics.*

object MaskCalibrator {
    fun normalizeDpi(bmp: Bitmap, sourceDpi: Int, targetDpi: Int): Bitmap {
        if (sourceDpi == targetDpi || sourceDpi <= 0 || targetDpi <= 0) return bmp
        val factor = targetDpi.toFloat() / sourceDpi.toFloat()
        val nw = (bmp.width * factor).toInt().coerceAtLeast(1)
        val nh = (bmp.height * factor).toInt().coerceAtLeast(1)
        return Bitmap.createScaledBitmap(bmp, nw, nh, true)
    }

    fun adjustBrightnessContrast(bmp: Bitmap, brightness: Float = 0f, contrast: Float = 1f): Bitmap {
        val cm = ColorMatrix(floatArrayOf(
            contrast, 0f, 0f, 0f, brightness,
            0f, contrast, 0f, 0f, brightness,
            0f, 0f, contrast, 0f, brightness,
            0f, 0f, 0f, 1f, 0f
        ))
        val out = Bitmap.createBitmap(bmp.width, bmp.height, bmp.config ?: Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { colorFilter = ColorMatrixColorFilter(cm) }
        canvas.drawBitmap(bmp, 0f, 0f, paint)
        return out
    }

    fun adaptMask(bmp: Bitmap): Bitmap {
        return adjustBrightnessContrast(bmp, 10f, 1.1f)
    }
}
