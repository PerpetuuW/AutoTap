package com.example.autotap.engine

import com.example.autotap.*

import android.graphics.Bitmap
import android.graphics.Rect
import android.os.Handler
import android.os.Looper
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.MyAutoClickService
import com.example.autotap.data.TemplateRepository
import java.util.concurrent.Executors

data class ScanResult(
    val match: MatchCandidate? = null,
    val score: Float = 0f,
    val jumpToStep: Int = -1,
    val targetScript: String = ""
)

class AiScannerEngine(private val service: MyAutoClickService) {

    private val templateRepository: TemplateRepository
        get() = TemplateRepository.instance

    private val uiHandler = Handler(Looper.getMainLooper())
    private val bgExecutor = Executors.newSingleThreadExecutor()

    @Volatile private var isCalibrating = false

    fun startTemplateCalibration(config: ActionConfig) {
        if (isCalibrating) return
        if (config.selectedTemplateIndex !in templateRepository.globalTemplates.indices) return

        isCalibrating = true
        MyAutoClickService.logAppEvent(service, "AI_SCANNER", "🔍 Запуск калибровки маски v35 шага #${config.id}")

        bgExecutor.execute {
            try {
                val template = templateRepository.globalTemplates[config.selectedTemplateIndex]
                val templatePath = templateRepository.globalTemplatesNames[config.selectedTemplateIndex]

                val fullBitmap = templateRepository.loadFullBitmap(templatePath)
                if (fullBitmap == null) {
                    finishCalibration()
                    return@execute
                }

                val calibrated = MaskCalibrator.calibrateMask(template, fullBitmap, config.dpi, config.dpi, true)
                val modes = SearchModes(
                    exactMatchOnly = config.exactMatchOnly,
                    shapeOnlyMode = config.shapeOnlyMode,
                    hybridCascadeMode = config.hybridCascadeMode,
                    multiScaleSearch = config.multiScaleSearch,
                    isFastMode = config.isFastMode
                )

                val searchArea = if (config.customSearchArea) {
                    Rect(
                        (config.searchAreaXNorm * fullBitmap.width).toInt().coerceIn(0, fullBitmap.width - 1),
                        (config.searchAreaYNorm * fullBitmap.height).toInt().coerceIn(0, fullBitmap.height - 1),
                        ((config.searchAreaXNorm + config.searchAreaWNorm) * fullBitmap.width).toInt().coerceIn(1, fullBitmap.width),
                        ((config.searchAreaYNorm + config.searchAreaHNorm) * fullBitmap.height).toInt().coerceIn(1, fullBitmap.height)
                    )
                } else null

                val candidates = HybridCascadeMatcher.match(fullBitmap, calibrated, searchArea, modes)
                val best = CandidateSelector.selectBest(candidates)

                if (best != null) {
                    val pct = (best.score * 100).toInt()
                    MyAutoClickService.logAppEvent(service, "AI_SCANNER", "🎯 Калибровка v35 завершена: точность=$pct% | rect=${best.rect}")
                    uiHandler.post {
                        config.calibratedRectNorm = best.rect
                        service.vibrateFeedback(40L)
                    }
                }

            } catch (e: Exception) {
                MyAutoClickService.logError(service, e)
            } finally {
                finishCalibration()
            }
        }
    }

    private fun finishCalibration() { isCalibrating = false }

    fun scanForMatch(screenBitmap: Bitmap?, config: ActionConfig): MatchCandidate? {
        if (screenBitmap == null) return null
        if (config.selectedTemplateIndex !in templateRepository.globalTemplates.indices) return null

        val template = templateRepository.globalTemplates[config.selectedTemplateIndex]
        val templatePath = templateRepository.globalTemplatesNames[config.selectedTemplateIndex]

        val calibrated = MaskCalibrator.calibrateMask(template, screenBitmap, config.dpi, config.dpi, true)
        val modes = SearchModes(
            exactMatchOnly = config.exactMatchOnly,
            shapeOnlyMode = config.shapeOnlyMode,
            hybridCascadeMode = config.hybridCascadeMode,
            multiScaleSearch = config.multiScaleSearch,
            isFastMode = config.isFastMode
        )

        val searchArea = if (config.customSearchArea) {
            Rect(
                (config.searchAreaXNorm * screenBitmap.width).toInt().coerceIn(0, screenBitmap.width - 1),
                (config.searchAreaYNorm * screenBitmap.height).toInt().coerceIn(0, screenBitmap.height - 1),
                ((config.searchAreaXNorm + config.searchAreaWNorm) * screenBitmap.width).toInt().coerceIn(1, screenBitmap.width),
                ((config.searchAreaYNorm + config.searchAreaHNorm) * screenBitmap.height).toInt().coerceIn(1, screenBitmap.height)
            )
        } else null

        val candidates = HybridCascadeMatcher.match(screenBitmap, calibrated, searchArea, modes)
        val match = CandidateSelector.selectBest(candidates)

        if (match != null) {
            val scorePct = (match.score * 100).toInt()
            val cx = match.rect.centerX()
            val cy = match.rect.centerY()
            MyAutoClickService.logAppEvent(service, "AI_SCANNER", "🎯 МАТЧ V35 НАЙДЕН! Порог=${config.similarityPercent}% | Итог=$scorePct% | pos=($cx, $cy)")

            val rx = match.rect.left.coerceAtLeast(0)
            val ry = match.rect.top.coerceAtLeast(0)
            val rw = match.rect.width().coerceAtMost(screenBitmap.width - rx)
            val rh = match.rect.height().coerceAtMost(screenBitmap.height - ry)
            if (rw > 0 && rh > 0) {
                val patch = Bitmap.createBitmap(screenBitmap, rx, ry, rw, rh)
                templateRepository.recordSuccessfulMatch(templatePath, patch)
            }
        }

        return match
    }

    fun executeAiTriggerSequence(config: ActionConfig): ScanResult {
        try {
            val screen = service.captureScreenBitmap() ?: return ScanResult()
            val match = scanForMatch(screen, config)

            if (match != null) {
                service.debuggerOverlay.update(config)

                if (config.playAudioOnMatch) {
                    service.vibrateFeedback(40L)
                }

                if (config.clickAiTarget) {
                    val cx = match.rect.centerX().toFloat()
                    val cy = match.rect.centerY().toFloat()
                    service.performClickWithCallback(cx, cy, service.globalClickDurationMs)
                }

                return ScanResult(
                    match = match,
                    score = match.score,
                    jumpToStep = config.jumpToStepOnMatch,
                    targetScript = config.targetScriptToLoad
                )
            }

        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
        }

        return ScanResult()
    }
}
