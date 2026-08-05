package com.example.autotap.ui.base

import com.example.autotap.*

enum class OverlayLayer(val zOrder: Int) {
    PANEL(100),
    JOYSTICK(200),
    CAPTURE(300),
    CANDIDATE(400),
    DEBUG(500),
    VISUALIZER(600)
}
