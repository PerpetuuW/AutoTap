package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Rect

class MaskCalibrator {

    private val contourExtractor = ContourExtractor()

    fun calibrate(mask: Bitmap): CalibratedMask {
        val bbox = Rect(0, 0, mask.width, mask.height)
        val contour = contourExtractor.extract(mask)
        val metadata = TemplateMetadata(
            boundingBox = bbox,
            contour = contour,
            calibratedRect = bbox
        )
        return CalibratedMask(
            original = mask,
            contour = contour,
            boundingBox = bbox,
            calibratedRect = bbox,
            metadata = metadata
        )
    }
}
