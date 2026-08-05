import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Интегрирован модуль v36.4 Enterprise: {rel_path}")

def deploy_v36_4_hybrid_cascade():
    print("🚀 Развертывание HybridCascadeMatcher v35 и 4 финальных модулей (v36.4.0-PRO)...")

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
        versionCode = 2470
        versionName = "36.4.0-PRO"

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

    # 2. SearchModes.kt (Модель режимов поиска)
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

    # 3. MaskCalibrator.kt (CalibratedMask)
    calibrator_code = r"""package com.example.autotap.engine

import android.graphics.*
import com.example.autotap.data.TemplateMetadata

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
        val downMask = Bitmap.createScaledBitmap(bitmap, (bitmap.width * 0.5f).toInt().coerceAtLeast(1), (bitmap.height * 0.5f).toInt().coerceAtLeast(1), true)
        val downFrame = Bitmap.createScaledBitmap(frame, (frame.width * 0.5f).toInt().coerceAtLeast(1), (frame.height * 0.5f).toInt().coerceAtLeast(1), true)

        val metadata = TemplateMetadata(
            width = bitmap.width,
            height = bitmap.height,
            dpi = targetDpi,
            scale = 1.0f,
            boundingBox = Rect(0, 0, bitmap.width, bitmap.height),
            isCircleShape = isCircle
        )

        return CalibratedMask(
            originalMask = bitmap,
            downscaledMask = downMask,
            downscaledFrame = downFrame,
            multiScaleMasks = listOf(Pair(1.0f, bitmap), Pair(0.5f, downMask)),
            contourPoints = emptyList(),
            metadata = metadata
        )
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/MaskCalibrator.kt", calibrator_code)

    # 4. HybridCascadeMatcher.kt (Реализация предложенного каркаса v35)
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

    # 5. GestureExecutor.kt (Модуль 1: Расширенный GestureExecutor)
    gesture_code = r"""package com.example.autotap.core

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.graphics.PointF
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator

class GestureExecutor(private val service: AccessibilityService) {

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

    fun performClickWithCallback(x: Float, y: Float, duration: Long = 100L, onComplete: ((Boolean) -> Unit)? = null) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }
        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) { onComplete?.invoke(true) }
            override fun onCancelled(gestureDescription: GestureDescription?) { onComplete?.invoke(false) }
        }, null)
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        performPathSwipeWithCallback(emptyList(), startX, startY, endX, endY, duration, onComplete)
    }

    fun performPathSwipeWithCallback(pathPoints: List<PointF>, startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }
        val path = Path().apply {
            if (pathPoints.size >= 2) {
                moveTo(pathPoints.first().x, pathPoints.first().y)
                for (i in 1 until pathPoints.size) lineTo(pathPoints[i].x, pathPoints[i].y)
            } else {
                moveTo(startX, startY)
                lineTo(endX, endY)
            }
        }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) { onComplete?.invoke(true) }
            override fun onCancelled(gestureDescription: GestureDescription?) { onComplete?.invoke(false) }
        }, null)
    }

    fun performMultiTouchWithCallback(pointers: List<PointF>, duration: Long = 200L, onComplete: ((Boolean) -> Unit)? = null) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N || pointers.isEmpty()) {
            onComplete?.invoke(false)
            return
        }
        val builder = GestureDescription.Builder()
        for (pt in pointers) {
            val path = Path().apply { moveTo(pt.x, pt.y) }
            builder.addStroke(GestureDescription.StrokeDescription(path, 0, duration))
        }

        service.dispatchGesture(builder.build(), object : AccessibilityService.GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) { onComplete?.invoke(true) }
            override fun onCancelled(gestureDescription: GestureDescription?) { onComplete?.invoke(false) }
        }, null)
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/core/GestureExecutor.kt", gesture_code)

    # 6. ScenarioDebuggerOverlay.kt (Модуль 3: Canvas-отладчик v35)
    debugger_code = r"""package com.example.autotap.ui.debug

import android.graphics.*
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority

class ScenarioDebuggerOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.scenario_debugger_overlay, OverlayLayer.DEBUG, OverlayPriority.HIGH) {

    private var debugView: DebugCanvasView? = null

    override fun onViewInflated(view: View) {
        debugView = view.findViewById(R.id.debugCanvasView)
    }

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }
    }

    fun update(config: ActionConfig) {
        if (!isShowing) show()
        debugView?.updateConfig(config)
    }

    private class DebugCanvasView(context: android.content.Context) : View(context) {
        private var cfg: ActionConfig? = null

        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.CYAN
            textSize = 34f
            typeface = Typeface.DEFAULT_BOLD
        }

        private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        private val heatPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            alpha = 70
        }

        fun updateConfig(config: ActionConfig) {
            cfg = config
            invalidate()
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val c = cfg ?: return
            val svc = MyAutoClickService.instance ?: return

            canvas.drawText("STEP #${c.id} [${c.type.name}] | Delay: ${c.delay}ms | Reps: ${c.repeatCount}", 40f, 100f, textPaint)

            when (c.type) {
                ActionType.CLICK, ActionType.LONG_PRESS, ActionType.HOLD -> {
                    val pt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                    strokePaint.color = Color.GREEN
                    canvas.drawCircle(pt.first, pt.second, 40f, strokePaint)
                    canvas.drawText("Target (${pt.first.toInt()}, ${pt.second.toInt()})", pt.first + 50f, pt.second, textPaint)
                }

                ActionType.SWIPE, ActionType.SWIPE_PATH -> {
                    val startPt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                    val endPt = svc.resolveNormalizedPoint(c.endXNorm, c.endYNorm)

                    strokePaint.color = Color.CYAN
                    canvas.drawCircle(startPt.first, startPt.second, 25f, strokePaint)
                    canvas.drawCircle(endPt.first, endPt.second, 25f, strokePaint)
                    canvas.drawLine(startPt.first, startPt.second, endPt.first, endPt.second, strokePaint)

                    if (c.joystickPath.isNotEmpty()) {
                        strokePaint.color = Color.MAGENTA
                        val path = Path()
                        val first = c.joystickPath.first()
                        val fPt = svc.resolveNormalizedPoint(first.x, first.y)
                        path.moveTo(fPt.first, fPt.second)

                        for (p in c.joystickPath.drop(1)) {
                            val pPt = svc.resolveNormalizedPoint(p.x, p.y)
                            path.lineTo(pPt.first, pPt.second)
                            canvas.drawCircle(pPt.first, pPt.second, 6f, strokePaint)
                        }
                        canvas.drawPath(path, strokePaint)
                    }
                }

                ActionType.TRIGGER -> {
                    if (c.customSearchArea) {
                        val startPt = svc.resolveNormalizedPoint(c.searchAreaXNorm, c.searchAreaYNorm)
                        val endPt = svc.resolveNormalizedPoint(c.searchAreaXNorm + c.searchAreaWNorm, c.searchAreaYNorm + c.searchAreaHNorm)

                        strokePaint.color = Color.YELLOW
                        val rect = RectF(startPt.first, startPt.second, endPt.first, endPt.second)
                        canvas.drawRect(rect, strokePaint)
                        canvas.drawText("Search Area (${c.similarityPercent}%)", startPt.first + 10f, startPt.second + 40f, textPaint)
                    }

                    c.calibratedRectNorm?.let { r ->
                        val startPt = svc.resolveNormalizedPoint(r.left.toFloat(), r.top.toFloat())
                        val endPt = svc.resolveNormalizedPoint(r.right.toFloat(), r.bottom.toFloat())

                        strokePaint.color = Color.RED
                        heatPaint.color = Color.RED
                        val rect = RectF(startPt.first, startPt.second, endPt.first, endPt.second)
                        canvas.drawRect(rect, heatPaint)
                        canvas.drawRect(rect, strokePaint)
                        canvas.drawText("Calibrated Mask Box", startPt.first + 10f, startPt.second + 40f, textPaint)
                    }
                }

                ActionType.WAIT -> {
                    canvas.drawText("WAIT State: ${c.waitType} (${c.holdDuration}ms)", 40f, 160f, textPaint)
                }

                ActionType.LOOP -> {
                    canvas.drawText("LOOP State: ${c.loopType} [Reps: ${c.loopCount}] -> Step #${c.loopStartIndex}", 40f, 160f, textPaint)
                }
            }
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt", debugger_code)

    print("✨ HybridCascadeMatcher v35 и 4 ключевых модуля успешно развернуты!")

if __name__ == "__main__":
    deploy_v36_4_hybrid_cascade()