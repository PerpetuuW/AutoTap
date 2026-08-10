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

        // 1. ПЕРВАЯ ПОПЫТКА НА ЦЕЛЕВОМ ПОРОГЕ (например, 85%)
        var candidates = if (!action.customSearchArea) {
            val hotspotArea = buildAnchorHotspotArea(action, frame, mask)
            val hotspotCandidates = cascadeMatcher.match(frame, mask, hotspotArea, searchModes, threshold)
            if (hotspotCandidates.isNotEmpty()) {
                logDiagnostic("AI_SCANNER", "Локальный якорь: цель найдена в исходной зоне!")
                hotspotCandidates
            } else {
                val fullArea = buildProfileAwareSearchArea(action, frame, profile, mask)
                cascadeMatcher.match(frame, mask, fullArea, searchModes, threshold)
            }
        } else {
            val fullArea = buildProfileAwareSearchArea(action, frame, profile, mask)
            cascadeMatcher.match(frame, mask, fullArea, searchModes, threshold)
        }

        // 2. АВТОМАШИНА АДАПТИВНОЙ КАЛИБРОВКИ (Снижение порога если нет совпадений)
        if (candidates.isEmpty()) {
            val adaptiveThreshold = (threshold - 0.15f).coerceAtLeast(0.55f)
            logDiagnostic("AI_SCANNER", "Авто-Калибровка: на пороге ${(threshold * 100).toInt()}% нет совпадений. Адаптивное снижение порога до ${(adaptiveThreshold * 100).toInt()}%...")

            candidates = if (!action.customSearchArea) {
                val hotspotArea = buildAnchorHotspotArea(action, frame, mask)
                val softHotspot = cascadeMatcher.match(frame, mask, hotspotArea, searchModes, adaptiveThreshold)
                if (softHotspot.isNotEmpty()) softHotspot
                else {
                    val fullArea = buildProfileAwareSearchArea(action, frame, profile, mask)
                    cascadeMatcher.match(frame, mask, fullArea, searchModes, adaptiveThreshold)
                }
            } else {
                val fullArea = buildProfileAwareSearchArea(action, frame, profile, mask)
                cascadeMatcher.match(frame, mask, fullArea, searchModes, adaptiveThreshold)
            }

            if (candidates.isNotEmpty()) {
                val best = candidates.maxByOrNull { it.score }
                logDiagnostic("AI_SCANNER", "🎯 Адаптивная калибровка УСПЕШНА: цель найдена с уверенностью ${((best?.score ?: 0f) * 100).toInt()}%!")
            }
        }

        return rankCandidates(candidates)
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

            val hotspotArea = if (!action.customSearchArea) buildAnchorHotspotArea(action, frame, mask) else buildProfileAwareSearchArea(action, frame, profile, mask)
            var candidates = cascadeMatcher.match(frame, mask, hotspotArea, searchModes, threshold)

            // Адаптивная калибровка для каждого шаблона
            if (candidates.isEmpty()) {
                val adaptiveThreshold = (threshold - 0.15f).coerceAtLeast(0.55f)
                candidates = cascadeMatcher.match(frame, mask, hotspotArea, searchModes, adaptiveThreshold)
            }

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

        val paddingX = (frame.width * 0.20f).toInt().coerceAtLeast(mask.width * 2)
        val paddingY = (frame.height * 0.20f).toInt().coerceAtLeast(mask.height * 2)

        return Rect(
            (anchorX - paddingX).coerceIn(0, frame.width),
            (anchorY - paddingY).coerceIn(0, frame.height),
            (anchorX + paddingX).coerceIn(0, frame.width),
            (anchorY + paddingY).coerceIn(0, frame.height)
        )
    }

    private fun buildProfileAwareModes(action: ActionConfig, profile: TemplateProfile): SearchModes {
        return SearchModes(
            shapeOnlyMode = action.shapeOnlyMode,
            autoTuningMode = true,
            hybridCascadeMode = action.hybridCascadeMode,
            multiScaleSearch = action.multiScaleSearch,
            contourWeight = 0.3f,
            pixelWeight = 0.7f,
            scaleBoost = 0.0f,
            profile = profile
        )
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
