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

        val match = candidates.firstOrNull()
        if (match != null && screenBitmap != null) {
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

    fun scanMultiTemplates(
        screenBitmap: Bitmap?,
        config: ActionConfig
    ): MatchCandidate? {
        if (screenBitmap == null) return null
        if (config.multiTemplateIndices.isEmpty()) return null

        var best: MatchCandidate? = null
        var bestPath: String? = null

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
                    bestPath = templatePath
                }
            }
        }

        if (best != null && bestPath != null && screenBitmap != null) {
            val rx = best.rect.left.coerceAtLeast(0)
            val ry = best.rect.top.coerceAtLeast(0)
            val rw = best.rect.width().coerceAtMost(screenBitmap.width - rx)
            val rh = best.rect.height().coerceAtMost(screenBitmap.height - ry)
            if (rw > 0 && rh > 0) {
                val patch = Bitmap.createBitmap(screenBitmap, rx, ry, rw, rh)
                templateRepository.recordSuccessfulMatch(bestPath, patch)
            }
        }

        return best
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
