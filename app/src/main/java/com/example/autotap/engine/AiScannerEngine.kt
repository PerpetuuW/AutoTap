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
            logDiagnostic("AI_SCANNER", "Пропуск: асинхронное сканирование уже выполняется.")
            callback(null)
            return
        }
        isScanning = true
        Thread {
            try {
                val result = scan(frameProvider, action)
                lastScanResult = result
                callback(result.point)
            } catch (e: Exception) {
                logError("AI_SCANNER", "Ошибка в scanAsync", e)
                callback(null)
            } finally {
                isScanning = false
            }
        }.start()
    }

    fun scan(frameProvider: () -> Bitmap?, action: ActionConfig): AiScanResult {
        val frame = frameProvider()
        if (frame == null) {
            logDiagnostic("AI_SCANNER", "Снимок экрана недоступен.")
            return AiScanResult(null, emptyList())
        }

        val candidates = if (action.multiTemplateIndices.isNotEmpty()) {
            templateMatcher.matchMultiTemplate(frame, action)
        } else {
            templateMatcher.matchSingleTemplate(frame, action)
        }

        if (candidates.isEmpty()) {
            logDiagnostic("AI_SCANNER", "Совпадений по маскам не найдено.")
            return AiScanResult(null, emptyList())
        }

        val bestCandidate = candidates.first()
        logDiagnostic("AI_SCANNER", "ИИ нашел целей: ${candidates.size}. Высший шаблон #${bestCandidate.templateIndex} (score=${"%.2f".format(bestCandidate.score)}) в $bestCandidate")
        return AiScanResult(bestCandidate.point, candidates)
    }
}
