package com.example.autotap.core

import com.example.autotap.MyAutoClickService
import com.example.autotap.engine.GestureExecutor as EngineGestureExecutor

class GestureExecutor(private val service: MyAutoClickService) {
    private val engineExecutor = EngineGestureExecutor(service)

    fun performClickSync(x: Float, y: Float, durationMs: Long): Boolean {
        return engineExecutor.performClickSync(x, y, durationMs)
    }

    fun performClick(x: Float, y: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        engineExecutor.performClick(x, y, durationMs, callback)
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long, callback: ((Boolean) -> Unit)? = null) {
        engineExecutor.performSwipeWithCallback(startX, startY, endX, endY, durationMs, callback)
    }
}
