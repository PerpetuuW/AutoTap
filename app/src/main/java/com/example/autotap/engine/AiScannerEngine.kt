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
        val frames = captureFrames(frameProvider, action)
        if (frames.isEmpty()) {
            logDiagnostic("AI_SCANNER", "Кадры не захвачены.")
            return AiScanResult(null, emptyList())
        }

        val allCandidates = mutableListOf<MatchCandidate>()
        for (frame in frames) {
            val candidates = templateMatcher.matchSingleTemplate(frame, action)
            allCandidates.addAll(candidates)
        }

        if (allCandidates.isEmpty()) {
            logDiagnostic("AI_SCANNER", "Совпадения не найдены.")
            return AiScanResult(null, emptyList())
        }

        val ranked = templateMatcher.rankCandidates(allCandidates)
        val stablePoint = computeStablePoint(ranked)

        logDiagnostic("AI_SCANNER", "Найдено кандидатов: ${ranked.size}, стабильная точка: $stablePoint")
        return AiScanResult(stablePoint, ranked)
    }

    private fun captureFrames(frameProvider: () -> Bitmap?, action: ActionConfig): List<Bitmap> {
        val frames = mutableListOf<Bitmap>()
        val frameCount = 3
        for (i in 0 until frameCount) {
            val frame = frameProvider()
            if (frame != null) {
                frames.add(frame)
            }
            val intervalMs = (action.scanIntervalSeconds * 1000L).toLong().coerceAtLeast(30L)
            try {
                Thread.sleep(intervalMs)
            } catch (_: Exception) {}
        }
        return frames
    }

    private fun computeStablePoint(candidates: List<MatchCandidate>): PointF? {
        if (candidates.isEmpty()) return null
        val best = candidates.first()
        return best.point
    }
}
