package com.example.autotap.engine

import android.graphics.*
import com.example.autotap.data.TemplateMetadata

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
        val downMask = Bitmap.createScaledBitmap(bitmap, (bitmap.width * 0.5f).toInt().coerceAtLeast(1), (bitmap.height * 0.5f).toInt().coerceAtLeast(1), true)
        val downFrame = Bitmap.createScaledBitmap(frame, (frame.width * 0.5f).toInt().coerceAtLeast(1), (frame.height * 0.5f).toInt().coerceAtLeast(1), true)

        val metadata = TemplateMetadata(
            width = bitmap.width,
            height = bitmap.height,
            dpi = targetDpi,
            scale = 1.0f,
            boundingBox = Rect(0, 0, bitmap.width, bitmap.height),
            isCircleShape = isCircle
        )

        return CalibratedMask(
            originalMask = bitmap,
            downscaledMask = downMask,
            downscaledFrame = downFrame,
            multiScaleMasks = listOf(Pair(1.0f, bitmap), Pair(0.5f, downMask)),
            contourPoints = emptyList(),
            metadata = metadata
        )
    }
}
