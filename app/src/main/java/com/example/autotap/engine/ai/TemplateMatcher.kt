package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Rect
import com.example.autotap.data.TemplateRepository
import com.example.autotap.model.ActionConfig

class TemplateMatcher(private val repository: TemplateRepository) {

    private val cascadeMatcher = HybridCascadeMatcher()

    fun matchSingleTemplate(frame: Bitmap, action: ActionConfig): List<MatchCandidate> {
        val mask = repository.loadTemplate(action.selectedTemplateIndex) ?: return emptyList()
        val searchArea = buildSearchArea(action, frame)
        val searchModes = SearchModes(
            shapeOnlyMode = action.shapeOnlyMode,
            autoTuningMode = action.autoTuningMode,
            hybridCascadeMode = action.hybridCascadeMode,
            multiScaleSearch = action.multiScaleSearch
        )

        return cascadeMatcher.match(frame, mask, searchArea, searchModes, action.similarityPercent / 100f)
    }

    fun rankCandidates(candidates: List<MatchCandidate>): List<MatchCandidate> {
        return candidates.sortedByDescending { it.score }
    }

    private fun buildSearchArea(action: ActionConfig, frame: Bitmap): Rect {
        return if (action.customSearchArea) {
            Rect(
                action.searchAreaX.coerceIn(0, frame.width),
                action.searchAreaY.coerceIn(0, frame.height),
                (action.searchAreaX + action.searchAreaW).coerceIn(0, frame.width),
                (action.searchAreaY + action.searchAreaH).coerceIn(0, frame.height)
            )
        } else {
            Rect(0, 0, frame.width, frame.height)
        }
    }
}
