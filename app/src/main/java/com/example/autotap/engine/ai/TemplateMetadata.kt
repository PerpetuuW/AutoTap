package com.example.autotap.engine.ai

import android.graphics.PointF
import android.graphics.Rect

data class TemplateMetadata(
    val dpi: Int = 420,
    val scale: Float = 1.0f,
    val boundingBox: Rect = Rect(),
    val contour: List<PointF> = emptyList(),
    val calibratedRect: Rect = Rect()
)
