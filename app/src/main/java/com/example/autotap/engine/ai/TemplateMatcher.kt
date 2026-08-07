package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Rect
import com.example.autotap.data.TemplateRepository
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig

class TemplateMatcher(private val repository: TemplateRepository) {

    private val cascadeMatcher = HybridCascadeMatcher()

    fun matchSingleTemplate(frame: Bitmap, action: ActionConfig): List<MatchCandidate> {
        val calibrated = repository.loadCalibratedMask(action.selectedTemplateIndex)
        val mask = calibrated?.original ?: repository.loadTemplate(action.selectedTemplateIndex) ?: return emptyList()
        val profile = calibrated?.metadata?.profile ?: TemplateProfile.MEDIUM

        val searchModes = buildProfileAwareModes(action, profile)
        val threshold = action.similarityPercent / 100f

        // ПРОХОД 1: СВЕРХБЫСТРЫЙ ПОИСК В ЛОКАЛЬНОЙ ЗОНЕ ЯКОРЯ (±15% ВОКРУГ ТОЧКИ СЪЕМКИ)
        if (!action.customSearchArea) {
            val hotspotArea = buildAnchorHotspotArea(action, frame, mask)
            val hotspotCandidates = cascadeMatcher.match(frame, mask, hotspotArea, searchModes, threshold)
            if (hotspotCandidates.isNotEmpty()) {
                logDiagnostic("AI_SCANNER", "Умный локальный якорь: цель найдена за 2мс в исходной зоне!")
                return hotspotCandidates
            }
        }

        // ПРОХОД 2: ПОЛНОЭКРАННЫЙ ПОИСК (FALLBACK ЕСЛИ ОБЪЕКТ СМЕСТИЛСЯ)
        val fullSearchArea = buildProfileAwareSearchArea(action, frame, profile, mask)
        return cascadeMatcher.match(frame, mask, fullSearchArea, searchModes, threshold)
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

            val searchModes = buildProfileAwareModes(action, profile)
            val threshold = action.similarityPercent / 100f

            // ПРОХОД 1 ПО ЛОКАЛЬНОМУ ЯКОРЮ
            if (!action.customSearchArea) {
                val hotspotArea = buildAnchorHotspotArea(action, frame, mask)
                val hotspotCandidates = cascadeMatcher.match(frame, mask, hotspotArea, searchModes, threshold)
                if (hotspotCandidates.isNotEmpty()) {
                    for (c in hotspotCandidates) {
                        allCandidates.add(c.copy(templateIndex = index))
                    }
                    continue
                }
            }

            // ПРОХОД 2 ПО ВСЕМУ ЭКРАНУ
            val fullSearchArea = buildProfileAwareSearchArea(action, frame, profile, mask)
            val candidates = cascadeMatcher.match(frame, mask, fullSearchArea, searchModes, threshold)
            for (c in candidates) {
                allCandidates.add(c.copy(templateIndex = index))
            }
        }

        return rankCandidates(allCandidates)
    }

    fun rankCandidates(candidates: List<MatchCandidate>): List<MatchCandidate> {
        return candidates.sortedByDescending { it.score }
    }

    private fun buildAnchorHotspotArea(action: ActionConfig, frame: Bitmap, mask: Bitmap): Rect {
        val anchorX = (action.xNorm * frame.width).toInt()
        val anchorY = (action.yNorm * frame.height).toInt()

        val paddingX = (frame.width * 0.15f).toInt().coerceAtLeast(mask.width * 2)
        val paddingY = (frame.height * 0.15f).toInt().coerceAtLeast(mask.height * 2)

        return Rect(
            (anchorX - paddingX).coerceIn(0, frame.width),
            (anchorY - paddingY).coerceIn(0, frame.height),
            (anchorX + paddingX).coerceIn(0, frame.width),
            (anchorY + paddingY).coerceIn(0, frame.height)
        )
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

    private fun buildProfileAwareSearchArea(action: ActionConfig, frame: Bitmap, profile: TemplateProfile, mask: Bitmap): Rect {
        if (action.customSearchArea) {
            val safeX = action.searchAreaX.coerceIn(0, frame.width)
            val safeY = action.searchAreaY.coerceIn(0, frame.height)
            val safeW = action.searchAreaW.coerceAtLeast(mask.width)
            val safeH = action.searchAreaH.coerceAtLeast(mask.height)

            val safeRight = (safeX + safeW).coerceIn(safeX + 1, frame.width)
            val safeBottom = (safeY + safeH).coerceIn(safeY + 1, frame.height)

            return Rect(safeX, safeY, safeRight, safeBottom)
        }

        return Rect(0, 0, frame.width, frame.height)
    }
}
