package com.example.autotap.engine

import com.example.autotap.ActionConfig

object ActionEditorEngine {
    fun validateAndNormalize(config: ActionConfig): ActionConfig {
        config.delay = config.delay.coerceAtLeast(50L)
        config.holdDuration = config.holdDuration.coerceAtLeast(100L)
        config.repeatCount = if (config.repeatCount == -1) -1 else config.repeatCount.coerceAtLeast(1)
        config.randomRadius = config.randomRadius.coerceAtLeast(0)
        config.similarityPercent = config.similarityPercent.coerceIn(10, 99)
        config.aiTimeoutSeconds = config.aiTimeoutSeconds.coerceAtLeast(1)
        config.scanIntervalSeconds = config.scanIntervalSeconds.coerceAtLeast(1)
        config.postMatchDelaySeconds = config.postMatchDelaySeconds.coerceAtLeast(0)
        config.xNorm = config.xNorm.coerceIn(0f, 1f)
        config.yNorm = config.yNorm.coerceIn(0f, 1f)
        config.endXNorm = config.endXNorm.coerceIn(0f, 1f)
        config.endYNorm = config.endYNorm.coerceIn(0f, 1f)
        return config
    }
}
