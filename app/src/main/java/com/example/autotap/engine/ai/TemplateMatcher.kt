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

        // 💥 ФИКС: При выключенной кастомной зоне ищем ПО ВСЕМУ ЭКРАНУ без ограничений!
        val searchArea = buildProfileAwareSearchArea(action, frame, profile, mask)
        logDiagnostic("AI_SCANNER", "Область поиска для Маски #" + action.selectedTemplateIndex + ": (" + searchArea.left + ", " + searchArea.top + ", " + searchArea.width() + "x" + searchArea.height() + "px)")

        var candidates = cascadeMatcher.match(frame, mask, searchArea, searchModes, threshold)

        if (candidates.isEmpty()) {
            val adaptiveThreshold = (threshold - 0.15f).coerceAtLeast(0.50f)
            logDiagnostic("AI_SCANNER", "Авто-Калибровка: на пороге " + (threshold * 100).toInt() + "% нет совпадений. Снижение порога до " + (adaptiveThreshold * 100).toInt() + "%...")
            candidates = cascadeMatcher.match(frame, mask, searchArea, searchModes, adaptiveThreshold)

            if (candidates.isNotEmpty()) {
                val best = candidates.maxByOrNull { it.score }
                logDiagnostic("AI_SCANNER", "🎯 Адаптивная калибровка УСПЕШНА: цель найдена с уверенностью " + ((best?.score ?: 0f) * 100).toInt() + "%!")
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
            val searchArea = buildProfileAwareSearchArea(action, frame, profile, mask)

            var candidates = cascadeMatcher.match(frame, mask, searchArea, searchModes, threshold)

            if (candidates.isEmpty()) {
                val adaptiveThreshold = (threshold - 0.15f).coerceAtLeast(0.50f)
                candidates = cascadeMatcher.match(frame, mask, searchArea, searchModes, adaptiveThreshold)
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

    private fun buildProfileAwareModes(action: ActionConfig, profile: TemplateProfile): SearchModes {
        return SearchModes(
            shapeOnlyMode = action.shapeOnlyMode,
            autoTuningMode = true,
            hybridCascadeMode = action.hybridCascadeMode,
            multiScaleSearch = action.multiScaleSearch,
            contourWeight = 0.4f,
            pixelWeight = 0.6f,
            scaleBoost = 0.0f,
            profile = profile
        )
    }

    private fun buildProfileAwareSearchArea(action: ActionConfig, frame: Bitmap, profile: TemplateProfile, mask: Bitmap): Rect {
        if (action.customSearchArea && action.searchAreaW > 10 && action.searchAreaH > 10) {
            val safeX = action.searchAreaX.coerceIn(0, frame.width - 10)
            val safeY = action.searchAreaY.coerceIn(0, frame.height - 10)
            val safeW = action.searchAreaW.coerceAtLeast(mask.width)
            val safeH = action.searchAreaH.coerceAtLeast(mask.height)

            val safeRight = (safeX + safeW).coerceIn(safeX + 1, frame.width)
            val safeBottom = (safeY + safeH).coerceIn(safeY + 1, frame.height)

            return Rect(safeX, safeY, safeRight, safeBottom)
        }

        // По умолчанию ПОЛНЫЙ ЭКРАН
        return Rect(0, 0, frame.width, frame.height)
    }
}
