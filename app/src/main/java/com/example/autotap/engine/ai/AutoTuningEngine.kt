package com.example.autotap.engine.ai

import com.example.autotap.model.ActionConfig

class AutoTuningEngine {

    fun autoTune(action: ActionConfig, candidates: List<MatchCandidate>): ActionConfig {
        val tuned = action.copy()
        if (candidates.size > 5) {
            tuned.similarityPercent = (action.similarityPercent + 5).coerceAtMost(98)
        } else if (candidates.isEmpty()) {
            tuned.similarityPercent = (action.similarityPercent - 5).coerceAtLeast(50)
        }
        return tuned
    }
}
