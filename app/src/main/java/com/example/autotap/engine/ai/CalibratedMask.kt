package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.PointF
import android.graphics.Rect

data class CalibratedMask(
    val original: Bitmap,
    val contour: List<PointF> = emptyList(),
    val boundingBox: Rect = Rect(),
    val calibratedRect: Rect = Rect(),
    val metadata: TemplateMetadata = TemplateMetadata()
)
