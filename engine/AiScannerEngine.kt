package com.example.autotap.engine

import android.accessibilityservice.AccessibilityService
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.view.Display
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.TemplateMatcher
import java.io.File
import java.io.FileOutputStream
import java.util.Locale
import java.util.concurrent.CountDownLatch

class AiScannerEngine(private val service: MyAutoClickService) {

    fun executeAiTriggerSequence(action: ActionConfig): Int {
        var triggeredJumpStep = -1
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R || !service.isPlaying) return -1

        val startTime = System.currentTimeMillis()
        val timeoutMs = if (action.aiTimeoutSeconds > 0) action.aiTimeoutSeconds * 1000L else 4000L
        val postMatchMs = if (action.postMatchDelaySeconds <= 0) 2000L else action.postMatchDelaySeconds * 1000L

        val templatesToSearch = if (action.multiTemplateIndices.isNotEmpty()) {
            action.multiTemplateIndices.filter { it in service.globalTemplates.indices }
        } else {
            if (action.selectedTemplateIndex in service.globalTemplates.indices) listOf(action.selectedTemplateIndex) else emptyList()
        }

        if (templatesToSearch.isEmpty()) return -1

        var lastScreenHash = -1

        while (service.isPlaying) {
            val now = System.currentTimeMillis()
            if (action.aiTimeoutSeconds > 0 && (now - startTime) >= timeoutMs) {
                MyAutoClickService.logAppEvent(service, "AI_Timeout", "⏱ Таймаут ожидания ($timeoutMs мс) истек на шаге #${action.id}")
                break
            }

            var localMatchFound = false
            val screenshotLatch = CountDownLatch(1)

            service.takeScreenshot(
                Display.DEFAULT_DISPLAY,
                service.bgScannerExecutor,
                object : AccessibilityService.TakeScreenshotCallback {
                    override fun onSuccess(screenshotResult: AccessibilityService.ScreenshotResult) {
                        val hwBuffer = screenshotResult.hardwareBuffer
                        try {
                            if (!service.isPlaying) return

                            val hwBitmap = Bitmap.wrapHardwareBuffer(hwBuffer, screenshotResult.colorSpace)
                            val softwareBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                            if (softwareBitmap != null) {
                                val currentHash = service.computeFastBitmapHash(softwareBitmap)
                                if (currentHash == lastScreenHash && action.aiTimeoutSeconds > 0) {
                                    MyAutoClickService.logAppEvent(service, "AI_SmartSkip", "⏩ Кадр уже проверялся для шага #${action.id}, умный переход далее")
                                    softwareBitmap.recycle()
                                    return
                                }
                                lastScreenHash = currentHash

                                var bestGlobalMatch: MatchCandidate? = null

                                for (tIdx in templatesToSearch) {
                                    if (!service.isPlaying) break

                                    val template = service.globalTemplates[tIdx]
                                    val meta = service.templateRepository.loadTemplateMetadata(service.globalTemplatesNames[tIdx])

                                    // полный Vision Engine: multi‑scale + hybrid/shape + heatmap
                                    val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(softwareBitmap, template, meta, action)
                                    if (candidates.isEmpty()) continue

                                    val verified = candidates.filter { cand ->
                                        TemplateMatcher.verifyHeatmapPeak(softwareBitmap, cand, template)
                                    }.sortedByDescending { it.score }

                                    val localBest = (if (verified.isNotEmpty()) verified else candidates).first()

                                    if (bestGlobalMatch == null || localBest.score > bestGlobalMatch!!.score) {
                                        bestGlobalMatch = localBest
                                    }
                                }

                                if (bestGlobalMatch != null && service.isPlaying) {
                                    val match = bestGlobalMatch!!
                                    localMatchFound = true

                                    val realMetrics = android.util.DisplayMetrics()
                                    service.overlayManager.windowManager.defaultDisplay.getRealMetrics(realMetrics)
                                    val scaleX = softwareBitmap.width.toFloat() / realMetrics.widthPixels.toFloat()
                                    val scaleY = softwareBitmap.height.toFloat() / realMetrics.heightPixels.toFloat()

                                    val clickX = match.point.x.toFloat() / scaleX
                                    val clickY = match.point.y.toFloat() / scaleY

                                    service.showClickVisualizer(clickX, clickY)

                                    if (action.clickAiTarget && service.isPlaying) {
                                        service.gestureExecutor.performClickWithCallback(clickX, clickY, service.globalClickDurationMs)
                                    }
                                }
                                softwareBitmap.recycle()
                            }
                        } catch (e: Exception) {
                            MyAutoClickService.logError(service, e)
                        } finally {
                            hwBuffer.close()
                            screenshotLatch.countDown()
                        }
                    }

                    override fun onFailure(errorCode: Int) {
                        screenshotLatch.countDown()
                    }
                }
            )

            try { screenshotLatch.await() } catch (_: Exception) {}

            if (!service.isPlaying) break

            if (localMatchFound) {
                if (triggeredJumpStep != -1 || !service.isPlaying) break
                try { Thread.sleep(postMatchMs) } catch (_: Exception) { break }
                break
            }

            val scanIntervalMs = (action.scanIntervalSeconds * 1000L).coerceAtLeast(300L)
            try { Thread.sleep(scanIntervalMs) } catch (_: Exception) { break }
        }

        return triggeredJumpStep
    }

    fun startTemplateCalibration(config: ActionConfig) {
        if (config.selectedTemplateIndex !in service.globalTemplates.indices) return

        val progressView = LayoutInflater.from(service).inflate(R.layout.floating_calibration_box, null)
        val tvProgress = progressView.findViewById<TextView>(R.id.tvCandidatePercent)
        tvProgress?.text = "Сканирование экрана..."

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        )
        service.overlayManager.safeAddView(progressView, params)
        service.controlPanelView?.visibility = View.INVISIBLE

        Handler(Looper.getMainLooper()).postDelayed({
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                service.takeScreenshot(
                    Display.DEFAULT_DISPLAY,
                    service.bgScannerExecutor,
                    object : AccessibilityService.TakeScreenshotCallback {
                        override fun onSuccess(screenshotResult: AccessibilityService.ScreenshotResult) {
                            val hwBuffer = screenshotResult.hardwareBuffer
                            try {
                                val hwBitmap = Bitmap.wrapHardwareBuffer(hwBuffer, screenshotResult.colorSpace)
                                val softwareBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                                if (softwareBitmap != null) {
                                    service.bgScannerExecutor.execute {
                                        runSmartCalibration(softwareBitmap, config, tvProgress, progressView)
                                    }
                                }
                            } catch (e: Exception) {
                                service.uiExecutor.execute {
                                    service.overlayManager.safeRemoveView(progressView)
                                    service.controlPanelView?.visibility = View.VISIBLE
                                }
                            } finally {
                                hwBuffer.close()
                            }
                        }

                        override fun onFailure(errorCode: Int) {
                            service.uiExecutor.execute {
                                service.overlayManager.safeRemoveView(progressView)
                                service.controlPanelView?.visibility = View.VISIBLE
                            }
                        }
                    }
                )
            }
        }, 300L)
    }

    private fun runSmartCalibration(
        bitmap: Bitmap,
        config: ActionConfig,
        tvProgress: TextView?,
        progressView: View?
    ) {
        val template = service.globalTemplates[config.selectedTemplateIndex]
        val templatePath = service.globalTemplatesNames[config.selectedTemplateIndex]
        val meta = service.templateRepository.loadTemplateMetadata(templatePath)
        val isCircle = meta?.optBoolean("isCircleShape", true) ?: true

        service.uiExecutor.execute { tvProgress?.text = "Поиск кандидатов..." }

        val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(bitmap, template, meta, config)

        service.uiExecutor.execute {
            service.overlayManager.safeRemoveView(progressView)
            if (candidates.isEmpty()) {
                Toast.makeText(service, "Кандидаты не найдены! Сделайте новый снимок маски.", Toast.LENGTH_LONG).show()
                service.controlPanelView?.visibility = View.VISIBLE
                service.showEditDialog(config)
                bitmap.recycle()
                return@execute
            }
            showCandidatesSelectionOverlay(bitmap, template, candidates, isCircle, config, templatePath)
        }
    }

    private fun showCandidatesSelectionOverlay(
        screenshot: Bitmap,
        smartMask: Bitmap,
        candidates: List<MatchCandidate>,
        isCircle: Boolean,
        existingConfig: ActionConfig?,
        existingTemplatePath: String?
    ) {
        service.removeCandidateSelectionOverlay()

        val realMetrics = android.util.DisplayMetrics()
        service.overlayManager.windowManager.defaultDisplay.getRealMetrics(realMetrics)
        val scaleX = screenshot.width.toFloat() / realMetrics.widthPixels.toFloat()
        val scaleY = screenshot.height.toFloat() / realMetrics.heightPixels.toFloat()

        val overlayView = FrameLayout(service).apply {
            setBackgroundColor(Color.parseColor("#40000000"))
            clipChildren = false
            clipToPadding = false
        }
        service.candidateSelectionOverlayView = overlayView

        val topBar = LinearLayout(service).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setBackgroundColor(Color.parseColor("#F00D1117"))
            setPadding(service.overlayManager.dpToPx(12), service.overlayManager.dpToPx(48), service.overlayManager.dpToPx(12), service.overlayManager.dpToPx(10))

            val tvTitle = TextView(service).apply {
                text = if (existingConfig == null) "Выберите лучший вариант маски" else "Выберите вариант калибровки"
                setTextColor(Color.WHITE)
                textSize = 14f
                setTypeface(null, android.graphics.Typeface.BOLD)
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f)
            }
            addView(tvTitle)

            val btnClose = Button(service).apply {
                text = "✕"
                setTextColor(Color.WHITE)
                textSize = 14f
                setTypeface(null, android.graphics.Typeface.BOLD)
                backgroundTintList = ColorStateList.valueOf(Color.parseColor("#F04438"))
                layoutParams = LinearLayout.LayoutParams(service.overlayManager.dpToPx(32), service.overlayManager.dpToPx(32))
                setPadding(0, 0, 0, 0)
                setOnClickListener {
                    service.vibrateFeedback(25L)
                    service.removeCandidateSelectionOverlay()
                    service.controlPanelView?.visibility = View.VISIBLE
                    if (existingConfig != null) service.showEditDialog(existingConfig)
                    screenshot.recycle()
                }
            }
            addView(btnClose)
        }

        val topBarParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        ).apply { gravity = Gravity.TOP }
        overlayView.addView(topBar, topBarParams)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        for (cand in candidates) {
            val screenW = (cand.rect.width() / scaleX).toInt().coerceAtLeast(service.overlayManager.dpToPx(36))
            val screenH = (cand.rect.height() / scaleY).toInt().coerceAtLeast(service.overlayManager.dpToPx(36))

            val maxLeft = (realMetrics.widthPixels - screenW - service.overlayManager.dpToPx(8)).coerceAtLeast(service.overlayManager.dpToPx(4))
            val maxTop = (realMetrics.heightPixels - screenH - service.overlayManager.dpToPx(40)).coerceAtLeast(service.overlayManager.dpToPx(60))

            val screenLeft = (cand.rect.left / scaleX).toInt().coerceIn(service.overlayManager.dpToPx(4), maxLeft)
            val screenTop = (cand.rect.top / scaleY).toInt().coerceIn(service.overlayManager.dpToPx(60), maxTop)

            val pctInt = (cand.score * 100).toInt().coerceIn(1, 99)
            val strokeColor = when {
                pctInt >= 85 -> Color.parseColor("#34C759")
                pctInt >= 70 -> Color.parseColor("#FFB703")
                else -> Color.parseColor("#FF3B30")
            }

            val candBox = FrameLayout(service).apply {
                clipChildren = false
                clipToPadding = false

                val borderView = View(service).apply {
                    val gd = android.graphics.drawable.GradientDrawable().apply {
                        setStroke(service.overlayManager.dpToPx(3.5f), strokeColor)
                        setColor(Color.TRANSPARENT)
                        cornerRadius = service.overlayManager.dpToPx(6).toFloat()
                    }
                    background = gd
                    layoutParams = FrameLayout.LayoutParams(screenW, screenH)
                }
                addView(borderView)

                val tvScore = TextView(service).apply {
                    text = "$pctInt%"
                    setTextColor(strokeColor)
                    textSize = 11f
                    setTypeface(null, android.graphics.Typeface.BOLD)
                    gravity = Gravity.CENTER
                    setShadowLayer(3f, 1f, 1f, Color.BLACK)
                    background = null
                    setPadding(service.overlayManager.dpToPx(2), 0, service.overlayManager.dpToPx(2), 0)
                }

                val scoreTopMargin = if (screenTop < service.overlayManager.dpToPx(80)) service.overlayManager.dpToPx(2) else -service.overlayManager.dpToPx(18)
                val scoreParams = FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                    topMargin = scoreTopMargin
                }
                addView(tvScore, scoreParams)

                setOnClickListener {
                    service.vibrateFeedback(30L)
                    service.removeCandidateSelectionOverlay()

                    service.bgScannerExecutor.execute {
                        try {
                            val cropW = cand.rect.width()
                            val cropH = cand.rect.height()
                            val safeX = cand.rect.left.coerceAtLeast(0)
                            val safeY = cand.rect.top.coerceAtLeast(0)
                            val safeW = cropW.coerceAtMost(screenshot.width - safeX)
                            val safeH = cropH.coerceAtMost(screenshot.height - safeY)

                            val cropped = Bitmap.createBitmap(screenshot, safeX, safeY, safeW, safeH)
                            val finalSmartMask = TemplateMatcher.generateSmartMask(cropped, isCircle)

                            val ts = System.currentTimeMillis()
                            val tPath = existingTemplatePath ?: File(File(service.filesDir, "templates/default").apply { mkdirs() }, "mask_$ts.png").absolutePath
                            val fPath = existingTemplatePath?.replace("mask_", "full_") ?: File(File(service.filesDir, "templates/default").apply { mkdirs() }, "full_$ts.png").absolutePath

                            FileOutputStream(File(tPath)).use { out -> finalSmartMask.compress(Bitmap.CompressFormat.PNG, 100, out) }
                            if (existingConfig == null) {
                                FileOutputStream(File(fPath)).use { out -> screenshot.compress(Bitmap.CompressFormat.PNG, 100, out) }
                            }

                            val metaFile = service.templateRepository.getTemplateMetadataFile(tPath)
                            val meta = TemplateMatcher.analyzeTemplate(cropped)
                            meta.put("similarityPercent", pctInt)
                            meta.put("originX", safeX)
                            meta.put("originY", safeY)
                            meta.put("originW", safeW)
                            meta.put("originH", safeH)
                            meta.put("isCircleShape", isCircle)
                            FileOutputStream(metaFile).use { out -> out.write(meta.toString().toByteArray()) }

                            service.uiExecutor.execute {
                                service.loadAllTemplatesFromDisk()
                                if (existingConfig != null) {
                                    existingConfig.similarityPercent = pctInt
                                    Toast.makeText(service, "✅ Шаблон калиброван ($pctInt%)!", Toast.LENGTH_SHORT).show()
                                    service.showEditDialog(existingConfig)
                                }
                                service.controlPanelView?.visibility = View.VISIBLE
                            }
                            cropped.recycle()
                            finalSmartMask.recycle()
                            screenshot.recycle()
                        } catch (e: Exception) {
                            MyAutoClickService.logError(service, e)
                        }
                    }
                }
            }

            val candParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                leftMargin = screenLeft
                topMargin = screenTop
            }
            overlayView.addView(candBox, candParams)
        }

        service.overlayManager.safeAddView(overlayView, params)
    }
}
