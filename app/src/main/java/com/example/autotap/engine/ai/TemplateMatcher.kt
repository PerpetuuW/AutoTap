package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Rect
import com.example.autotap.data.TemplateRepository
import com.example.autotap.model.ActionConfig

class TemplateMatcher(private val repository: TemplateRepository) {

    private val cascadeMatcher = HybridCascadeMatcher()

    fun matchSingleTemplate(frame: Bitmap, action: ActionConfig): List<MatchCandidate> {
        val calibrated = repository.loadCalibratedMask(action.selectedTemplateIndex)
        val mask = calibrated?.original ?: repository.loadTemplate(action.selectedTemplateIndex) ?: return emptyList()
        val profile = calibrated?.metadata?.profile ?: TemplateProfile.MEDIUM

        val searchArea = buildProfileAwareSearchArea(action, frame, profile)
        val searchModes = buildProfileAwareModes(action, profile)

        return cascadeMatcher.match(frame, mask, searchArea, searchModes, action.similarityPercent / 100f)
    }

    fun matchMultiTemplate(frame: Bitmap, action: ActionConfig): List<MatchCandidate> {
        val indices = if (action.multiTemplateIndices.isNotEmpty()) {
            action.multiTemplateIndices
        } else {
            listOf(action.selectedTemplateIndex)
        }

        val allCandidates = mutableListOf<MatchCandidate>()

        for (index in indices) {
            val calibrated = repository.loadCalibratedMask(index)
            val mask = calibrated?.original ?: repository.loadTemplate(index) ?: continue
            val profile = calibrated?.metadata?.profile ?: TemplateProfile.MEDIUM

            val searchArea = buildProfileAwareSearchArea(action, frame, profile)
            val searchModes = buildProfileAwareModes(action, profile)

            val candidates = cascadeMatcher.match(frame, mask, searchArea, searchModes, action.similarityPercent / 100f)
            for (c in candidates) {
                allCandidates.add(c.copy(templateIndex = index))
            }
        }

        return rankCandidates(allCandidates)
    }

    fun rankCandidates(candidates: List<MatchCandidate>): List<MatchCandidate> {
        return candidates.sortedByDescending { it.score }
    }

    private fun buildProfileAwareModes(action: ActionConfig, profile: TemplateProfile): SearchModes {
        return when (profile) {
            TemplateProfile.SMALL -> SearchModes(
                shapeOnlyMode = action.shapeOnlyMode,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = action.multiScaleSearch,
                contourWeight = 0.4f,
                pixelWeight = 0.6f,
                scaleBoost = 0.25f,
                profile = profile
            )
            TemplateProfile.LARGE -> SearchModes(
                shapeOnlyMode = action.shapeOnlyMode,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = action.multiScaleSearch,
                contourWeight = 0.2f,
                pixelWeight = 0.8f,
                scaleBoost = -0.25f,
                profile = profile
            )
            TemplateProfile.THIN_LINE -> SearchModes(
                shapeOnlyMode = true,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = false,
                contourWeight = 0.85f,
                pixelWeight = 0.15f,
                scaleBoost = 0.0f,
                profile = profile
            )
            else -> SearchModes(
                shapeOnlyMode = action.shapeOnlyMode,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = action.multiScaleSearch,
                contourWeight = 0.3f,
                pixelWeight = 0.7f,
                scaleBoost = 0.0f,
                profile = profile
            )
        }
    }

    private fun buildProfileAwareSearchArea(action: ActionConfig, frame: Bitmap, profile: TemplateProfile): Rect {
        if (action.customSearchArea) {
            return Rect(
                action.searchAreaX.coerceIn(0, frame.width),
                action.searchAreaY.coerceIn(0, frame.height),
                (action.searchAreaX + action.searchAreaW).coerceIn(0, frame.width),
                (action.searchAreaY + action.searchAreaH).coerceIn(0, frame.height)
            )
        }

        return Rect(0, 0, frame.width, frame.height)
    }
}
