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

    fun scanAsync(frameProvider: () -> Bitmap?, action: ActionConfig, callback: (PointF?) -> Unit) {
        if (isScanning) {
            logDiagnostic("AI_SCANNER", "Пропуск: сканирование уже выполняется.")
            callback(null)
            return
        }
        isScanning = true
        Thread {
            try {
                val result = scan(frameProvider, action)
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
            logDiagnostic("AI_SCANNER", "Кадр экрана недоступен.")
            return AiScanResult(null, emptyList())
        }

        val candidates = if (action.multiTemplateIndices.isNotEmpty()) {
            templateMatcher.matchMultiTemplate(frame, action)
        } else {
            templateMatcher.matchSingleTemplate(frame, action)
        }

        if (candidates.isEmpty()) {
            logDiagnostic("AI_SCANNER", "Совпадений по шаблонам не найдено.")
            return AiScanResult(null, emptyList())
        }

        val bestCandidate = candidates.first()
        logDiagnostic("AI_SCANNER", "Мультипоиск: найден шаблон #${bestCandidate.templateIndex} со score=${"%.2f".format(bestCandidate.score)} в ${bestCandidate.point}")
        return AiScanResult(bestCandidate.point, candidates)
    }
}
