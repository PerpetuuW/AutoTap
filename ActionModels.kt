package com.example.autotap

import android.graphics.Point
import android.graphics.PointF
import android.graphics.Rect
import android.view.View

enum class ActionType { CLICK, LONG_PRESS, SWIPE, TRIGGER, JOYSTICK_PATH }

enum class TemplateType {
    MICRO, SMALL, MEDIUM, LARGE, HUGE, THIN_HORIZONTAL, THIN_VERTICAL, WIDE, STANDARD
}

data class MatchCandidate(
    val point: Point = Point(),
    val ratio: Float = 0f,
    val rect: Rect = Rect()
) {
    val score: Float get() = ratio
    constructor(point: Point, rect: Rect, ratio: Float) : this(point, ratio, rect)
    constructor(rect: Rect, ratio: Float) : this(Point(rect.centerX(), rect.centerY()), ratio, rect)
}

class ActionConfig(
    var id: Int,
    var startView: View,
    var type: ActionType = ActionType.CLICK,
    var delay: Long = 1000,
    var checkInterval: Long = 500,
    var endView: View? = null,
    var selectedTemplateIndex: Int = -1,
    var clickAiTarget: Boolean = true,
    var jumpToStepOnMatch: Int = 0,
    var captureSize: Int = 100,
    var repeatCount: Int = 1,
    var holdDuration: Long = 1000,
    var randomRadius: Int = 0,
    var fullScreenshotPath: String = "",
    var maskX: Int = 0,
    var maskY: Int = 0,
    var maskW: Int = 100,
    var maskH: Int = 100,
    var similarityPercent: Int = 70,
    var targetScriptToLoad: String = "",
    var aiTimeoutSeconds: Int = 4,
    var scanIntervalSeconds: Int = 5,
    var postMatchDelaySeconds: Int = 3,
    var multiTemplateIndices: ArrayList<Int> = arrayListOf(),
    var searchInCapturedArea: Boolean = false,
    var playAudioOnMatch: Boolean = false,
    var isFastMode: Boolean = true,
    var bestMatchAuto: Boolean = true,
    var exactMatchOnly: Boolean = false,
    var semiTransparentMode: Boolean = false,
    var showSearchVisualizer: Boolean = true,
    var customSearchArea: Boolean = false,
    var searchAreaX: Int = 0,
    var searchAreaY: Int = 0,
    var searchAreaW: Int = 0,
    var searchAreaH: Int = 0,
    var shapeOnlyMode: Boolean = false,
    var hybridCascadeMode: Boolean = true,
    var searchAreasList: ArrayList<Rect> = arrayListOf(),
    var joystickPath: ArrayList<PointF> = arrayListOf(),
    var centerOfMassClick: Boolean = false,
    var multiScaleSearch: Boolean = false,
    var autoTuningMode: Boolean = false
)
