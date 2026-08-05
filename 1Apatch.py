import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан модуль: {rel_path}")

def finalize_v35_calibrated_mask_and_ai():
    print("🚀 Перевод CalibratedMask, MaskCalibrator и AiScannerEngine на 100% стандарт v35 (v36.10.0-PRO)...")

    # 1. app/build.gradle.kts
    gradle_code = r"""plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.autotap"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.autotap"
        minSdk = 24
        targetSdk = 35
        versionCode = 2530
        versionName = "36.10.0-PRO"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("com.google.android.material:material:1.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
"""
    write_file("app/build.gradle.kts", gradle_code)

    # 2. SearchModes.kt
    search_modes_code = r"""package com.example.autotap.engine

data class SearchModes(
    val exactMatchOnly: Boolean = false,
    val shapeOnlyMode: Boolean = false,
    val hybridCascadeMode: Boolean = true,
    val multiScaleSearch: Boolean = false,
    val isFastMode: Boolean = true
)
"""
    write_file("app/src/main/java/com/example/autotap/engine/SearchModes.kt", search_modes_code)

    # 3. MaskCalibrator.kt & CalibratedMask.kt (Структура v35)
    calibrator_code = r"""package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.PointF
import android.graphics.Rect
import com.example.autotap.data.TemplateMetadata
import kotlin.math.max
import kotlin.math.min

data class CalibratedMask(
    val originalMask: Bitmap,
    val downscaledMask: Bitmap,
    val downscaledFrame: Bitmap,
    val multiScaleMasks: List<Pair<Float, Bitmap>>,
    val contourPoints: List<PointF>,
    val metadata: TemplateMetadata
)

object MaskCalibrator {

    fun calibrateMask(
        bitmap: Bitmap,
        frame: Bitmap,
        sourceDpi: Int = 480,
        targetDpi: Int = 480,
        isCircle: Boolean = true
    ): CalibratedMask {
        val claheMask = applyClaheLocalContrast(bitmap)
        val downMask = Bitmap.createScaledBitmap(claheMask, (claheMask.width * 0.5f).toInt().coerceAtLeast(1), (claheMask.height * 0.5f).toInt().coerceAtLeast(1), true)
        val downFrame = Bitmap.createScaledBitmap(frame, (frame.width * 0.5f).toInt().coerceAtLeast(1), (frame.height * 0.5f).toInt().coerceAtLeast(1), true)

        val multiScale = listOf(
            Pair(1.0f, claheMask),
            Pair(0.75f, Bitmap.createScaledBitmap(claheMask, (claheMask.width * 0.75f).toInt().coerceAtLeast(1), (claheMask.height * 0.75f).toInt().coerceAtLeast(1), true)),
            Pair(0.5f, downMask)
        )

        val contour = extractContour(claheMask)

        val metadata = TemplateMetadata(
            width = bitmap.width,
            height = bitmap.height,
            dpi = targetDpi,
            scale = 1.0f,
            boundingBox = Rect(0, 0, bitmap.width, bitmap.height),
            isCircleShape = isCircle
        )

        return CalibratedMask(
            originalMask = claheMask,
            downscaledMask = downMask,
            downscaledFrame = downFrame,
            multiScaleMasks = multiScale,
            contourPoints = contour,
            metadata = metadata
        )
    }

    fun applyClaheLocalContrast(bmp: Bitmap): Bitmap {
        val out = bmp.copy(Bitmap.Config.ARGB_8888, true)
        val w = out.width
        val h = out.height
        val pixels = IntArray(w * h)
        out.getPixels(pixels, 0, w, 0, 0, w, h)

        for (i in pixels.indices) {
            val c = pixels[i]
            val r = Color.red(c)
            val g = Color.green(c)
            val b = Color.blue(c)
            val alpha = Color.alpha(c)

            val gray = (0.299f * r + 0.587f * g + 0.114f * b).toInt().coerceIn(0, 255)
            val enhanced = if (gray > 128) max(0, gray - 15) else minOf(255, gray + 15)
            pixels[i] = Color.argb(alpha, enhanced, enhanced, enhanced)
        }

        out.setPixels(pixels, 0, w, 0, 0, w, h)
        return out
    }

    private fun extractContour(bmp: Bitmap): List<PointF> {
        val list = ArrayList<PointF>()
        val w = bmp.width
        val h = bmp.height
        for (y in 0 until h step 4) {
            for (x in 0 until w step 4) {
                val alpha = Color.alpha(bmp.getPixel(x, y))
                if (alpha > 128) {
                    list.add(PointF(x.toFloat(), y.toFloat()))
                }
            }
        }
        return list
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/MaskCalibrator.kt", calibrator_code)

    # 4. HybridCascadeMatcher.kt
    cascade_code = r"""package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.PointF
import android.graphics.Rect
import com.example.autotap.MatchCandidate

object HybridCascadeMatcher {

    fun match(
        frame: Bitmap,
        calibratedMask: CalibratedMask,
        searchArea: Rect?,
        modes: SearchModes
    ): List<MatchCandidate> {

        val coarseCandidates = coarseMatch(
            frameDownscaled = calibratedMask.downscaledFrame,
            maskDownscaled = calibratedMask.downscaledMask,
            searchArea = searchArea
        )

        val fineCandidates = coarseCandidates.mapNotNull { coarse ->
            fineMatch(
                fullFrame = frame,
                fullMask = calibratedMask.originalMask,
                coarseRect = coarse.rect
            )
        }

        return rankCandidates(fineCandidates, modes)
    }

    private fun coarseMatch(
        frameDownscaled: Bitmap,
        maskDownscaled: Bitmap,
        searchArea: Rect?
    ): List<MatchCandidate> {

        val results = mutableListOf<MatchCandidate>()
        val w = (frameDownscaled.width - maskDownscaled.width).coerceAtLeast(1)
        val h = (frameDownscaled.height - maskDownscaled.height).coerceAtLeast(1)

        val area = searchArea ?: Rect(0, 0, w, h)

        for (y in area.top until area.bottom.coerceAtMost(h) step 2) {
            for (x in area.left until area.right.coerceAtMost(w) step 2) {

                val score = fastCompare(frameDownscaled, maskDownscaled, x, y)
                if (score > 0.55f) {
                    results.add(
                        MatchCandidate(
                            rect = Rect(x, y, x + maskDownscaled.width, y + maskDownscaled.height),
                            score = score
                        )
                    )
                }
            }
        }

        return results
    }

    private fun fineMatch(
        fullFrame: Bitmap,
        fullMask: Bitmap,
        coarseRect: Rect
    ): MatchCandidate? {

        val w = fullMask.width
        val h = fullMask.height

        val startX = (coarseRect.left * 2).coerceIn(0, (fullFrame.width - w).coerceAtLeast(0))
        val startY = (coarseRect.top * 2).coerceIn(0, (fullFrame.height - h).coerceAtLeast(0))

        var bestScore = 0f
        var bestX = -1
        var bestY = -1

        for (y in startY until (startY + 10).coerceAtMost(fullFrame.height - h + 1)) {
            for (x in startX until (startX + 10).coerceAtMost(fullFrame.width - w + 1)) {

                val score = preciseCompare(fullFrame, fullMask, x, y)
                if (score > bestScore) {
                    bestScore = score
                    bestX = x
                    bestY = y
                }
            }
        }

        if (bestX == -1) return null

        return MatchCandidate(
            rect = Rect(bestX, bestY, bestX + w, bestY + h),
            score = bestScore
        )
    }

    private fun rankCandidates(
        candidates: List<MatchCandidate>,
        modes: SearchModes
    ): List<MatchCandidate> {

        val sorted = candidates.sortedByDescending { it.score }

        return if (modes.exactMatchOnly) {
            sorted.filter { it.score > 0.92f }
        } else {
            sorted
        }
    }

    private fun fastCompare(
        frame: Bitmap,
        mask: Bitmap,
        x: Int,
        y: Int
    ): Float {
        var score = 0f
        val w = mask.width
        val h = mask.height

        for (dy in 0 until h step 3) {
            for (dx in 0 until w step 3) {
                if (x + dx < frame.width && y + dy < frame.height) {
                    if (frame.getPixel(x + dx, y + dy) == mask.getPixel(dx, dy)) {
                        score += 0.01f
                    }
                }
            }
        }

        return score.coerceIn(0f, 1f)
    }

    private fun preciseCompare(
        frame: Bitmap,
        mask: Bitmap,
        x: Int,
        y: Int
    ): Float {
        var score = 0f
        val w = mask.width
        val h = mask.height

        for (dy in 0 until h step 2) {
            for (dx in 0 until w step 2) {
                if (x + dx < frame.width && y + dy < frame.height) {
                    if (frame.getPixel(x + dx, y + dy) == mask.getPixel(dx, dy)) {
                        score += 0.005f
                    }
                }
            }
        }

        return score.coerceIn(0f, 1f)
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/HybridCascadeMatcher.kt", cascade_code)

    # 5. AiScannerEngine.kt
    ai_engine_code = r"""package com.example.autotap.engine

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
"""
    write_file("app/src/main/java/com/example/autotap/engine/AiScannerEngine.kt", ai_engine_code)

    print("✨ Перевод ИИ-модулей CalibratedMask, MaskCalibrator и AiScannerEngine на v35 Enterprise завершен!")

if __name__ == "__main__":
    finalize_v35_calibrated_mask_and_ai()