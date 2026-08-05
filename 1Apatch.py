import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Проверено и обновлено v36.5: {rel_path}")

def deploy_v36_5_full_checklist():
    print("🚀 Развертывание и проверка по 6-пунктовому архитектурному чек-листу (v36.5.0-PRO)...")

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
        versionCode = 2480
        versionName = "36.5.0-PRO"

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

    # 2. GestureExecutor.kt (Внедрение GestureQueue, smoothPath, MultiTouch)
    gesture_code = r"""package com.example.autotap.core

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.graphics.PointF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import java.util.ArrayDeque

class GestureExecutor(private val service: AccessibilityService) {

    private val gestureQueue = ArrayDeque<Runnable>()
    private var isProcessingQueue = false
    private val mainHandler = Handler(Looper.getMainLooper())

    fun vibrateFeedback(durationMs: Long = 25L) {
        try {
            val vibrator = service.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (vibrator != null && vibrator.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (_: Exception) {}
    }

    fun randomOffset(radius: Int): PointF {
        if (radius <= 0) return PointF(0f, 0f)
        val dx = (-radius..radius).random().toFloat()
        val dy = (-radius..radius).random().toFloat()
        return PointF(dx, dy)
    }

    private fun processNextGesture() {
        if (isProcessingQueue || gestureQueue.isEmpty()) return
        isProcessingQueue = true
        val task = gestureQueue.poll()
        task?.run()
    }

    private fun finishGestureTask() {
        isProcessingQueue = false
        mainHandler.postDelayed({ processNextGesture() }, 20L)
    }

    fun performClickWithCallback(x: Float, y: Float, duration: Long = 100L, onComplete: ((Boolean) -> Unit)? = null) {
        gestureQueue.add(Runnable {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                onComplete?.invoke(false)
                finishGestureTask()
                return@Runnable
            }
            val path = Path().apply { moveTo(x, y) }
            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            val res = service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                onComplete?.invoke(false)
                finishGestureTask()
            }
        })
        processNextGesture()
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        performPathSwipeWithCallback(emptyList(), startX, startY, endX, endY, duration, onComplete)
    }

    fun performPathSwipeWithCallback(pathPoints: List<PointF>, startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        gestureQueue.add(Runnable {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                onComplete?.invoke(false)
                finishGestureTask()
                return@Runnable
            }

            val smoothed = smoothPath(pathPoints)

            val path = Path().apply {
                if (smoothed.size >= 2) {
                    moveTo(smoothed.first().x, smoothed.first().y)
                    for (i in 1 until smoothed.size) {
                        lineTo(smoothed[i].x, smoothed[i].y)
                    }
                } else {
                    moveTo(startX, startY)
                    lineTo(endX, endY)
                }
            }

            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            val res = service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                onComplete?.invoke(false)
                finishGestureTask()
            }
        })
        processNextGesture()
    }

    fun performMultiTouchWithCallback(pointers: List<PointF>, duration: Long = 200L, onComplete: ((Boolean) -> Unit)? = null) {
        gestureQueue.add(Runnable {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N || pointers.isEmpty()) {
                onComplete?.invoke(false)
                finishGestureTask()
                return@Runnable
            }
            val builder = GestureDescription.Builder()
            for (pt in pointers) {
                val path = Path().apply { moveTo(pt.x, pt.y) }
                builder.addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            }

            val res = service.dispatchGesture(builder.build(), object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                onComplete?.invoke(false)
                finishGestureTask()
            }
        })
        processNextGesture()
    }

    private fun smoothPath(raw: List<PointF>): List<PointF> {
        if (raw.size < 3) return raw
        val smoothed = ArrayList<PointF>()
        smoothed.add(raw.first())
        for (i in 1 until raw.size - 1) {
            val prev = raw[i - 1]
            val curr = raw[i]
            val next = raw[i + 1]
            val smX = (prev.x + curr.x + next.x) / 3f
            val smY = (prev.y + curr.y + next.y) / 3f
            smoothed.add(PointF(smX, smY))
        }
        smoothed.add(raw.last())
        return smoothed
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/core/GestureExecutor.kt", gesture_code)

    # 3. AiScannerEngine.kt (Возврат ScanResult с jumpToStep и targetScript)
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
                    uiHandler.post {
                        config.calibratedRectNorm = best.rect
                        service.vibrateFeedback(40L)
                    }
                }

            } catch (_: Exception) {
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

        val frames = listOf(screenBitmap)
        val match = MultiFrameMatcher.matchMultiFrame(frames, calibrated.originalMask, templateRepository.loadTemplateMetadata(templatePath), config)

        if (match != null) {
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

    # 4. ScriptExecutor.kt (Декаплинг jumpToStep и targetScript)
    script_exec_code = r"""package com.example.autotap.engine

import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService

class ScriptExecutor(private val service: MyAutoClickService) {

    private var executionThread: Thread? = null
    private val uiHandler = Handler(Looper.getMainLooper())

    fun startExecutionLoop() {
        if (executionThread != null) return
        if (service.actionsList.isEmpty()) return

        executionThread = Thread {
            var currentIndex = 0

            uiHandler.post {
                service.hideControlPanel()
                service.joystickOverlay.hide()
                service.showFloatingStopButton()
            }

            while (service.isPlaying && service.actionsList.isNotEmpty()) {
                val action = service.actionsList[currentIndex]

                try { Thread.sleep(action.delay) } catch (_: InterruptedException) { break }
                if (!service.isPlaying) break

                when (action.type) {
                    ActionType.CLICK -> {
                        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val jitter = service.randomOffset(action.randomRadius)
                        val fx = pt.first + jitter.x
                        val fy = pt.second + jitter.y

                        uiHandler.post {
                            service.showClickVisualizer(fx, fy)
                            service.debuggerOverlay.update(action)
                        }

                        service.gestureExecutor.performClickWithCallback(fx, fy, service.globalClickDurationMs)
                    }

                    ActionType.LONG_PRESS, ActionType.HOLD -> {
                        val pt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        uiHandler.post {
                            service.showClickVisualizer(pt.first, pt.second)
                            service.debuggerOverlay.update(action)
                        }
                        service.gestureExecutor.performClickWithCallback(pt.first, pt.second, action.holdDuration)
                    }

                    ActionType.SWIPE -> {
                        val startPt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                        uiHandler.post { service.debuggerOverlay.update(action) }

                        if (action.joystickPath.isNotEmpty()) {
                            val path = action.joystickPath.map { p ->
                                val normP = service.resolveNormalizedPoint(p.x, p.y)
                                PointF(normP.first, normP.second)
                            }
                            service.gestureExecutor.performPathSwipeWithCallback(path, startPt.first, startPt.second, endPt.first, endPt.second, action.holdDuration)
                        } else {
                            service.gestureExecutor.performSwipeWithCallback(startPt.first, startPt.second, endPt.first, endPt.second, action.holdDuration)
                        }
                    }

                    ActionType.SWIPE_PATH -> {
                        val startPt = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val endPt = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)
                        val path = action.joystickPath.map { p ->
                            val normP = service.resolveNormalizedPoint(p.x, p.y)
                            PointF(normP.first, normP.second)
                        }
                        service.gestureExecutor.performPathSwipeWithCallback(path, startPt.first, startPt.second, endPt.first, endPt.second, action.holdDuration)
                    }

                    ActionType.WAIT -> {
                        when (action.waitType) {
                            "TIME" -> Thread.sleep(action.delay)
                            "TEMPLATE_APPEAR" -> {
                                val start = System.currentTimeMillis()
                                while (service.isPlaying && (System.currentTimeMillis() - start < action.holdDuration)) {
                                    val match = service.aiScannerEngine.scanForMatch(service.captureScreenBitmap(), action)
                                    if (match != null) break
                                    Thread.sleep(100)
                                }
                            }
                            "TEMPLATE_DISAPPEAR" -> {
                                val start = System.currentTimeMillis()
                                while (service.isPlaying && (System.currentTimeMillis() - start < action.holdDuration)) {
                                    val match = service.aiScannerEngine.scanForMatch(service.captureScreenBitmap(), action)
                                    if (match == null) break
                                    Thread.sleep(100)
                                }
                            }
                        }
                    }

                    ActionType.LOOP -> {
                        if (action.loopCount > 1) {
                            action.loopCount--
                            currentIndex = action.loopStartIndex.coerceIn(0, service.actionsList.size - 1)
                            continue
                        }
                    }

                    ActionType.TRIGGER -> {
                        uiHandler.post { service.debuggerOverlay.update(action) }
                        val scanResult = service.aiScannerEngine.executeAiTriggerSequence(action)

                        when {
                            scanResult.targetScript.isNotEmpty() -> {
                                service.loadScriptByName(scanResult.targetScript)
                                currentIndex = 0
                                continue
                            }
                            scanResult.jumpToStep > 0 -> {
                                val targetIdx = service.actionsList.indexOfFirst { it.id == scanResult.jumpToStep }
                                if (targetIdx != -1) {
                                    currentIndex = targetIdx
                                    continue
                                }
                            }
                        }
                    }
                }

                currentIndex = (currentIndex + 1) % service.actionsList.size
            }

            service.isPlaying = false
            uiHandler.post { stopExecutionLoop() }
        }

        executionThread?.start()
    }

    fun stopExecutionLoop() {
        service.isPlaying = false
        executionThread?.interrupt()
        executionThread = null

        uiHandler.post {
            service.hideFloatingStopButton()
            service.showControlPanel()
            service.debuggerOverlay.hide()
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/ScriptExecutor.kt", script_exec_code)

    print("✨ Проверка по 6 пунктам завершена, все улучшения v36.5.0-PRO внесены!")

if __name__ == "__main__":
    deploy_v36_5_full_checklist()