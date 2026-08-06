package com.example.autotap.model

data class TutorialStep(
    val hintText: String,
    val hintX: Int,
    val hintY: Int,
    val spotlightX: Int? = null,
    val spotlightY: Int? = null,
    val arrowX: Int? = null,
    val arrowY: Int? = null
)
