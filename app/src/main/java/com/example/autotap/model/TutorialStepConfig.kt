package com.example.autotap.model

import android.graphics.Rect

data class TutorialStepConfig(
    val id: String,
    val message: String,
    val highlightArea: Rect? = null,
    val waitForClickOnArea: Rect? = null,
    val autoAdvance: Boolean = false,
    val delayMs: Long = 0L
)
