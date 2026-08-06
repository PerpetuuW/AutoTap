package com.example.autotap.engine.ai

data class SearchModes(
    val exactMatchOnly: Boolean = false,
    val hybridCascadeMode: Boolean = true,
    val multiScaleSearch: Boolean = true,
    val autoTuningMode: Boolean = false,
    val shapeOnlyMode: Boolean = false,
    val allowWeakCandidates: Boolean = false,
    val contourWeight: Float = 0.3f,
    val pixelWeight: Float = 0.7f,
    val scaleBoost: Float = 0.0f,
    val profile: TemplateProfile = TemplateProfile.MEDIUM
)
