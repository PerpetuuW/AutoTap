package com.example.autotap.engine

import com.example.autotap.*

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.PointF
import android.graphics.Rect
import com.example.autotap.data.TemplateMetadata
import kotlin.math.max
import kotlin.math.min

data class CalibratedMask(
    val originalMask: Bitmap,
    val downscaledMask: Bitmap,
    val downscaledFrame: Bitmap,
    val multiScaleMasks: List<Pair<Float, Bitmap>>,
    val contourPoints: List<PointF>,
    val metadata: TemplateMetadata
)

object MaskCalibrator {

    fun calibrateMask(
        bitmap: Bitmap,
        frame: Bitmap,
        sourceDpi: Int = 480,
        targetDpi: Int = 480,
        isCircle: Boolean = true
    ): CalibratedMask {
        val claheMask = applyClaheLocalContrast(bitmap)
        val downMask = Bitmap.createScaledBitmap(claheMask, (claheMask.width * 0.5f).toInt().coerceAtLeast(1), (claheMask.height * 0.5f).toInt().coerceAtLeast(1), true)
        val downFrame = Bitmap.createScaledBitmap(frame, (frame.width * 0.5f).toInt().coerceAtLeast(1), (frame.height * 0.5f).toInt().coerceAtLeast(1), true)

        val multiScale = listOf(
            Pair(1.0f, claheMask),
            Pair(0.75f, Bitmap.createScaledBitmap(claheMask, (claheMask.width * 0.75f).toInt().coerceAtLeast(1), (claheMask.height * 0.75f).toInt().coerceAtLeast(1), true)),
            Pair(0.5f, downMask)
        )

        val contour = extractContour(claheMask)

        val metadata = TemplateMetadata(
            width = bitmap.width,
            height = bitmap.height,
            dpi = targetDpi,
            scale = 1.0f,
            boundingBox = Rect(0, 0, bitmap.width, bitmap.height),
            isCircleShape = isCircle
        )

        return CalibratedMask(
            originalMask = claheMask,
            downscaledMask = downMask,
            downscaledFrame = downFrame,
            multiScaleMasks = multiScale,
            contourPoints = contour,
            metadata = metadata
        )
    }

    fun adaptMask(bmp: Bitmap): Bitmap {
        return applyClaheLocalContrast(bmp)
    }

    fun applyClaheLocalContrast(bmp: Bitmap): Bitmap {
        val out = bmp.copy(Bitmap.Config.ARGB_8888, true)
        val w = out.width
        val h = out.height
        val pixels = IntArray(w * h)
        out.getPixels(pixels, 0, w, 0, 0, w, h)

        for (i in pixels.indices) {
            val c = pixels[i]
            val r = Color.red(c)
            val g = Color.green(c)
            val b = Color.blue(c)
            val alpha = Color.alpha(c)

            val gray = (0.299f * r + 0.587f * g + 0.114f * b).toInt().coerceIn(0, 255)
            val enhanced = if (gray > 128) max(0, gray - 15) else minOf(255, gray + 15)
            pixels[i] = Color.argb(alpha, enhanced, enhanced, enhanced)
        }

        out.setPixels(pixels, 0, w, 0, 0, w, h)
        return out
    }

    private fun extractContour(bmp: Bitmap): List<PointF> {
        val list = ArrayList<PointF>()
        val w = bmp.width
        val h = bmp.height
        for (y in 0 until h step 4) {
            for (x in 0 until w step 4) {
                val alpha = Color.alpha(bmp.getPixel(x, y))
                if (alpha > 128) {
                    list.add(PointF(x.toFloat(), y.toFloat()))
                }
            }
        }
        return list
    }
}
