package com.example.autotap.engine.ai

import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig

class AutoTuningEngine {

    fun adaptivelyTuneThreshold(
        action: ActionConfig,
        candidates: List<MatchCandidate>,
        scanFunction: (Float) -> List<MatchCandidate>
    ): List<MatchCandidate> {
        if (candidates.isNotEmpty()) return candidates
        if (!action.autoTuningMode) return candidates

        val currentThreshold = action.similarityPercent / 100f
        val softThreshold = (currentThreshold - 0.10f).coerceAtLeast(0.50f)

        logDiagnostic("AI_SCANNER", "AutoTuning: первая попытка не дала результатов. Адаптивное снижение порога до ${(softThreshold * 100).toInt()}%...")

        val softCandidates = scanFunction(softThreshold)
        if (softCandidates.isNotEmpty()) {
            val best = softCandidates.maxByOrNull { it.score }
            logDiagnostic("AI_SCANNER", "AutoTuning: цель успешно найдена адаптивно с уверенностью ${((best?.score ?: 0f) * 100).toInt()}%!")
        }
        return softCandidates
    }
}
