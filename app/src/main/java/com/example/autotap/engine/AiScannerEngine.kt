package com.example.autotap.engine

import android.graphics.Bitmap
import android.os.Handler
import android.os.Looper
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.MyAutoClickService
import com.example.autotap.TemplateMatcher
import com.example.autotap.data.TemplateRepository
import java.util.concurrent.Executors

class AiScannerEngine(private val service: MyAutoClickService) {

    private val templateRepository: TemplateRepository
        get() = service.templateRepository

    private val uiHandler = Handler(Looper.getMainLooper())
    private val bgExecutor = Executors.newSingleThreadExecutor()

    @Volatile
    private var isCalibrating = false

    fun startTemplateCalibration(config: ActionConfig) {
        if (isCalibrating) return
        if (config.selectedTemplateIndex !in templateRepository.globalTemplates.indices) return

        isCalibrating = true

        bgExecutor.execute {
            try {
                val template = templateRepository.globalTemplates[config.selectedTemplateIndex]
                val templatePath = templateRepository.globalTemplatesNames[config.selectedTemplateIndex]
                val meta = templateRepository.loadTemplateMetadata(templatePath)

                val fullBitmap = templateRepository.loadFullBitmap(templatePath)
                if (fullBitmap == null) {
                    finishCalibration()
                    return@execute
                }

                val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(
                    fullBitmap,
                    template,
                    meta,
                    config
                )

                val best = candidates.firstOrNull()
                if (best != null) {
                    uiHandler.post {
                        config.calibratedRectNorm = best.rect
                        service.gestureExecutor.vibrateFeedback(40L)
                    }
                }

            } catch (_: Exception) {
            } finally {
                finishCalibration()
            }
        }
    }

    private fun finishCalibration() {
        isCalibrating = false
    }

    fun scanForMatch(
        screenBitmap: Bitmap?,
        config: ActionConfig
    ): MatchCandidate? {
        if (screenBitmap == null) return null
        if (config.selectedTemplateIndex !in templateRepository.globalTemplates.indices) return null

        val template = templateRepository.globalTemplates[config.selectedTemplateIndex]
        val templatePath = templateRepository.globalTemplatesNames[config.selectedTemplateIndex]
        val meta = templateRepository.loadTemplateMetadata(templatePath)

        val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(
            screenBitmap,
            template,
            meta,
            config
        )

        return candidates.firstOrNull()
    }

    fun scanMultiTemplates(
        screenBitmap: Bitmap?,
        config: ActionConfig
    ): MatchCandidate? {
        if (screenBitmap == null) return null
        if (config.multiTemplateIndices.isEmpty()) return null

        var best: MatchCandidate? = null

        for (idx in config.multiTemplateIndices) {
            if (idx !in templateRepository.globalTemplates.indices) continue

            val template = templateRepository.globalTemplates[idx]
            val templatePath = templateRepository.globalTemplatesNames[idx]
            val meta = templateRepository.loadTemplateMetadata(templatePath)

            val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(
                screenBitmap,
                template,
                meta,
                config
            )

            val candidate = candidates.firstOrNull()
            if (candidate != null) {
                if (best == null || candidate.score > best!!.score) {
                    best = candidate
                }
            }
        }

        return best
    }

    fun scanWithTimeout(
        screenBitmap: Bitmap?,
        config: ActionConfig,
        timeoutMs: Long,
        callback: (MatchCandidate?) -> Unit
    ) {
        if (screenBitmap == null) {
            callback(null)
            return
        }

        val startTime = System.currentTimeMillis()

        bgExecutor.execute {
            var result: MatchCandidate? = null

            while (System.currentTimeMillis() - startTime < timeoutMs) {
                result = scanForMatch(screenBitmap, config)
                if (result != null) break
                Thread.sleep(50)
            }

            uiHandler.post { callback(result) }
        }
    }

    fun executeAiTriggerSequence(config: ActionConfig): Int {
        try {
            val screen = service.captureScreenBitmap() ?: return -1

            val match = if (config.multiTemplateIndices.isNotEmpty()) {
                scanMultiTemplates(screen, config)
            } else {
                scanForMatch(screen, config)
            }

            if (match != null) {
                if (config.playAudioOnMatch) {
                    service.gestureExecutor.vibrateFeedback(40L)
                }

                if (config.clickAiTarget) {
                    val cx = match.rect.centerX().toFloat()
                    val cy = match.rect.centerY().toFloat()
                    service.gestureExecutor.performClickWithCallback(cx, cy, service.globalClickDurationMs)
                }

                if (config.jumpToStepOnMatch > 0) {
                    return config.jumpToStepOnMatch
                }

                if (config.targetScriptToLoad.isNotEmpty()) {
                    service.loadScriptByName(config.targetScriptToLoad)
                    return -999
                }
            }

        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
        }

        return -1
    }
}
