package com.example.autotap.engine.ai

import android.graphics.PointF

data class AiScanResult(
    val point: PointF?,
    val candidates: List<MatchCandidate> = emptyList(),
    val jumpToStep: Int? = null,
    val targetScriptToLoad: String? = null
)
