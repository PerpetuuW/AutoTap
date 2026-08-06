package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Rect

class MaskCalibrator {

    private val contourExtractor = ContourExtractor()

    fun calibrate(mask: Bitmap): CalibratedMask {
        val width = mask.width
        val height = mask.height
        val bbox = Rect(0, 0, width, height)
        val contour = contourExtractor.extract(mask)

        val profile = detectProfile(width, height)

        val metadata = TemplateMetadata(
            boundingBox = bbox,
            contour = contour,
            calibratedRect = bbox,
            profile = profile,
            layoutHints = getLayoutHintForProfile(profile)
        )

        return CalibratedMask(
            original = mask,
            contour = contour,
            boundingBox = bbox,
            calibratedRect = bbox,
            metadata = metadata
        )
    }

    private fun detectProfile(width: Int, height: Int): TemplateProfile {
        val area = width * height
        val maxDim = maxOf(width, height)
        val minDim = minOf(width, height)

        if (minDim > 0 && (maxDim.toFloat() / minDim.toFloat() > 4.5f)) {
            return TemplateProfile.THIN_LINE
        }

        if (maxDim <= 48 || area < 2300) {
            return TemplateProfile.SMALL
        }

        if (area > 200000 || (width > 600 && height > 400)) {
            return TemplateProfile.LARGE
        }

        return TemplateProfile.MEDIUM
    }

    private fun getLayoutHintForProfile(profile: TemplateProfile): String {
        return when (profile) {
            TemplateProfile.SMALL -> "TOOLBAR_OR_CORNERS"
            TemplateProfile.MEDIUM -> "CENTER_CARDS"
            TemplateProfile.LARGE -> "FULL_SCREEN"
            TemplateProfile.THIN_LINE -> "DIVIDERS_BORDERS"
            TemplateProfile.MIXED -> "ANY"
        }
    }
}
