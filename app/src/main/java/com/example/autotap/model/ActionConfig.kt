package com.example.autotap.model

import android.graphics.PointF

enum class ActionType {
    CLICK, SWIPE, LONG_PRESS, AI_SEARCH, WAIT, LOAD_SCRIPT, JOYSTICK_PATH
}

data class ActionConfig(
    var type: ActionType = ActionType.CLICK,
    var xNorm: Float = 0.5f,
    var yNorm: Float = 0.5f,
    var endXNorm: Float = 0.5f,
    var endYNorm: Float = 0.5f,
    var randomRadius: Float = 0f,
    var delay: Long = 500L,
    var holdDuration: Long = 100L,
    var selectedTemplateIndex: Int = 0,
    var multiTemplateIndices: List<Int> = emptyList(),
    var similarityPercent: Int = 85,
    var scanIntervalSeconds: Float = 0.1f,
    var clickAiTarget: Boolean = false,
    var loopUntilStopped: Boolean = true,
    var jumpToStepOnMatch: Int? = null,
    var jumpToStepOnFail: Int? = null,
    var targetScriptToLoad: String? = null,
    var customSearchArea: Boolean = false,
    var searchAreaX: Int = 0,
    var searchAreaY: Int = 0,
    var searchAreaW: Int = 0,
    var searchAreaH: Int = 0,
    var shapeOnlyMode: Boolean = false,
    var autoTuningMode: Boolean = false,
    var hybridCascadeMode: Boolean = true,
    var multiScaleSearch: Boolean = true,
    var joystickPath: List<PointF> = emptyList(),
    var swipePath: List<PointF> = emptyList(),
    var longPressDuration: Long = 500L,
    var clickOffsetX: Int = 0,
    var clickOffsetY: Int = 0,
    var notificationMode: Int = 0 // 0 = OFF, 1 = VIBRO, 2 = SOUND, 3 = BOTH
)
