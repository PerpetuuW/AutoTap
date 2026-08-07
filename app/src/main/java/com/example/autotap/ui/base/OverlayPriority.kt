package com.example.autotap.ui.base

enum class OverlayPriority(val zOrder: Int) {
    LOW(1),
    MEDIUM(5),
    NORMAL(5),
    HIGH(10),
    CRITICAL(20)
}
