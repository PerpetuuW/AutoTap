package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.PointF
import com.example.autotap.MyAutoClickService
import com.example.autotap.engine.ai.AiScanResult
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.engine.ai.TemplateMatcher
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig

class AiScannerEngine(private val service: MyAutoClickService) {

    private val templateMatcher by lazy { TemplateMatcher(service.templateRepository) }
    @Volatile private var isScanning = false
    @Volatile var lastScanResult: AiScanResult? = null
        private set

    fun scanAsync(frameProvider: () -> Bitmap?, action: ActionConfig, callback: (PointF?) -> Unit) {
        if (isScanning) {
            logDiagnostic("AI_SCANNER", "[WARNING] Пропуск вызова scanAsync: предыдущий процесс сканирования еще активен (isScanning=true).")
            callback(null)
            return
        }
        isScanning = true
        Thread {
            try {
                val startTime = System.currentTimeMillis()
                val result = scan(frameProvider, action)
                val duration = System.currentTimeMillis() - startTime

                lastScanResult = result

                val candidates = result.candidates
                val reqPercent = action.similarityPercent

                if (candidates.isNotEmpty()) {
                    val best = candidates.first()
                    val bestPercent = (best.score * 100).toInt()
                    logDiagnostic(
                        "AI_SCANNER",
                        "🎯 Поиск Маски #${action.selectedTemplateIndex} ($duration мс): УСПЕХ! Найдено целей: ${candidates.size}. Высшая точность: $bestPercent% (Требуется: $reqPercent%) в точке (${best.point.x.toInt()}, ${best.point.y.toInt()})"
                    )
                } else {
                    logDiagnostic(
                        "AI_SCANNER",
                        "🔍 Поиск Маски #${action.selectedTemplateIndex} ($duration мс): Совпадений выше порога $reqPercent% НЕ найдено."
                    )
                }

                callback(result.point)
            } catch (e: Exception) {
                logError("AI_SCANNER", "Исключение во время работы scanAsync()", e)
                callback(null)
            } finally {
                isScanning = false
            }
        }.start()
    }

    fun scan(frameProvider: () -> Bitmap?, action: ActionConfig): AiScanResult {
        val frame = frameProvider()
        if (frame == null) {
            logError("AI_SCANNER", "Снимок экрана равен NULL. Сканирование отменено.", null)
            return AiScanResult(null, emptyList())
        }

        val candidates = if (action.multiTemplateIndices.isNotEmpty()) {
            logDiagnostic("AI_SCANNER", "Запуск мульти-поиска по маскам: ${action.multiTemplateIndices}")
            templateMatcher.matchMultiTemplate(frame, action)
        } else {
            logDiagnostic("AI_SCANNER", "Запуск одиночного поиска для Маски #${action.selectedTemplateIndex}")
            templateMatcher.matchSingleTemplate(frame, action)
        }

        if (candidates.isEmpty()) {
            return AiScanResult(null, emptyList())
        }

        val bestCandidate = candidates.first()
        return AiScanResult(bestCandidate.point, candidates)
    }
}
