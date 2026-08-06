package com.example.autotap.engine.ai

import android.graphics.PointF
import android.graphics.Rect

data class MatchCandidate(
    val point: PointF,
    val score: Float,
    val boundingBox: Rect,
    val scale: Float,
    val templateIndex: Int
)
