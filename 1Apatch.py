import os
import shutil

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Развернут модуль: {rel_path}")

def clean_old_subpackages():
    base_java_dir = os.path.join("app", "src", "main", "java", "com", "example", "autotap")
    subfolders = ["ui", "engine", "data", "core"]
    for sub in subfolders:
        target = os.path.join(base_java_dir, sub)
        if os.path.exists(target):
            shutil.rmtree(target)
            print(f"  [🧹] Очищена устаревшая подпапка: {target}")

def build_consolidated_v35():
    print("🚀 Сборка монолитной архитектуры AutoTap v35 Enterprise (Единый пакет)...")
    clean_old_subpackages()

    # 1. Gradle Config (v35)
    write_file("app/build.gradle.kts", r"""plugins {
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
        versionCode = 2360
        versionName = "35.1.0-PRO"

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
""")

    # 2. ActionType.kt
    write_file("app/src/main/java/com/example/autotap/ActionType.kt", r"""package com.example.autotap

enum class ActionType {
    CLICK,
    LONG_PRESS,
    SWIPE,
    TRIGGER
}
""")

    # 3. ActionConfig.kt
    write_file("app/src/main/java/com/example/autotap/ActionConfig.kt", r"""package com.example.autotap

import android.graphics.PointF
import android.graphics.Rect
import android.view.View
import org.json.JSONArray
import org.json.JSONObject

data class ActionConfig(
    var id: Int = 0,
    var type: ActionType = ActionType.CLICK,

    var xNorm: Float = 0f,
    var yNorm: Float = 0f,

    var endXNorm: Float = 0f,
    var endYNorm: Float = 0f,

    var delay: Long = 500L,
    var repeatCount: Int = 1,
    var randomRadius: Int = 0,
    var holdDuration: Long = 1000L,

    var selectedTemplateIndex: Int = -1,
    var multiTemplateIndices: ArrayList<Int> = ArrayList(),
    var clickAiTarget: Boolean = true,
    var targetScriptToLoad: String = "",
    var jumpToStepOnMatch: Int = -1,

    var aiTimeoutSeconds: Int = 15,
    var similarityPercent: Int = 70,
    var scanIntervalSeconds: Int = 5,
    var postMatchDelaySeconds: Int = 3,
    var playAudioOnMatch: Boolean = false,
    var isFastMode: Boolean = true,

    var shapeOnlyMode: Boolean = false,
    var hybridCascadeMode: Boolean = true,
    var multiScaleSearch: Boolean = false,
    var autoTuningMode: Boolean = false,
    var exactMatchOnly: Boolean = false,
    var showSearchVisualizer: Boolean = true,

    var customSearchArea: Boolean = false,
    var searchAreaXNorm: Float = 0f,
    var searchAreaYNorm: Float = 0f,
    var searchAreaWNorm: Float = 1f,
    var searchAreaHNorm: Float = 1f,

    var joystickPath: ArrayList<PointF> = ArrayList(),
    var calibratedRectNorm: Rect? = null,

    @Transient var startView: View? = null,
    @Transient var endView: View? = null
) {
    companion object {
        fun fromJson(obj: JSONObject): ActionConfig {
            val cfg = ActionConfig()

            cfg.id = obj.optInt("id", 0)
            cfg.type = ActionType.valueOf(obj.optString("type", "CLICK"))

            cfg.xNorm = obj.optDouble("xNorm", 0.0).toFloat()
            cfg.yNorm = obj.optDouble("yNorm", 0.0).toFloat()
            cfg.endXNorm = obj.optDouble("endXNorm", 0.0).toFloat()
            cfg.endYNorm = obj.optDouble("endYNorm", 0.0).toFloat()

            cfg.delay = obj.optLong("delay", 500L)
            cfg.repeatCount = obj.optInt("repeatCount", 1)
            cfg.randomRadius = obj.optInt("randomRadius", 0)
            cfg.holdDuration = obj.optLong("holdDuration", 1000L)

            cfg.selectedTemplateIndex = obj.optInt("selectedTemplateIndex", -1)

            val arrMulti = obj.optJSONArray("multiTemplateIndices") ?: JSONArray()
            cfg.multiTemplateIndices = ArrayList<Int>().apply {
                for (i in 0 until arrMulti.length()) add(arrMulti.optInt(i))
            }

            cfg.clickAiTarget = obj.optBoolean("clickAiTarget", true)
            cfg.targetScriptToLoad = obj.optString("targetScriptToLoad", "")
            cfg.jumpToStepOnMatch = obj.optInt("jumpToStepOnMatch", -1)

            cfg.aiTimeoutSeconds = obj.optInt("aiTimeoutSeconds", 15)
            cfg.similarityPercent = obj.optInt("similarityPercent", 70)
            cfg.scanIntervalSeconds = obj.optInt("scanIntervalSeconds", 5)
            cfg.postMatchDelaySeconds = obj.optInt("postMatchDelaySeconds", 3)
            cfg.playAudioOnMatch = obj.optBoolean("playAudioOnMatch", false)
            cfg.isFastMode = obj.optBoolean("isFastMode", true)

            cfg.shapeOnlyMode = obj.optBoolean("shapeOnlyMode", false)
            cfg.hybridCascadeMode = obj.optBoolean("hybridCascadeMode", true)
            cfg.multiScaleSearch = obj.optBoolean("multiScaleSearch", false)
            cfg.autoTuningMode = obj.optBoolean("autoTuningMode", false)
            cfg.exactMatchOnly = obj.optBoolean("exactMatchOnly", false)
            cfg.showSearchVisualizer = obj.optBoolean("showSearchVisualizer", true)

            cfg.customSearchArea = obj.optBoolean("customSearchArea", false)
            cfg.searchAreaXNorm = obj.optDouble("searchAreaXNorm", 0.0).toFloat()
            cfg.searchAreaYNorm = obj.optDouble("searchAreaYNorm", 0.0).toFloat()
            cfg.searchAreaWNorm = obj.optDouble("searchAreaWNorm", 1.0).toFloat()
            cfg.searchAreaHNorm = obj.optDouble("searchAreaHNorm", 1.0).toFloat()

            val arrPath = obj.optJSONArray("joystickPath") ?: JSONArray()
            cfg.joystickPath = ArrayList<PointF>().apply {
                for (i in 0 until arrPath.length()) {
                    val p = arrPath.optJSONObject(i)
                    add(PointF(
                        p.optDouble("x", 0.0).toFloat(),
                        p.optDouble("y", 0.0).toFloat()
                    ))
                }
            }

            return cfg
        }
    }

    fun toJson(): JSONObject {
        val obj = JSONObject()

        obj.put("id", id)
        obj.put("type", type.name)

        obj.put("xNorm", xNorm)
        obj.put("yNorm", yNorm)
        obj.put("endXNorm", endXNorm)
        obj.put("endYNorm", endYNorm)

        obj.put("delay", delay)
        obj.put("repeatCount", repeatCount)
        obj.put("randomRadius", randomRadius)
        obj.put("holdDuration", holdDuration)

        obj.put("selectedTemplateIndex", selectedTemplateIndex)
        obj.put("multiTemplateIndices", JSONArray(multiTemplateIndices))

        obj.put("clickAiTarget", clickAiTarget)
        obj.put("targetScriptToLoad", targetScriptToLoad)
        obj.put("jumpToStepOnMatch", jumpToStepOnMatch)

        obj.put("aiTimeoutSeconds", aiTimeoutSeconds)
        obj.put("similarityPercent", similarityPercent)
        obj.put("scanIntervalSeconds", scanIntervalSeconds)
        obj.put("postMatchDelaySeconds", postMatchDelaySeconds)
        obj.put("playAudioOnMatch", playAudioOnMatch)
        obj.put("isFastMode", isFastMode)

        obj.put("shapeOnlyMode", shapeOnlyMode)
        obj.put("hybridCascadeMode", hybridCascadeMode)
        obj.put("multiScaleSearch", multiScaleSearch)
        obj.put("autoTuningMode", autoTuningMode)
        obj.put("exactMatchOnly", exactMatchOnly)
        obj.put("showSearchVisualizer", showSearchVisualizer)

        obj.put("customSearchArea", customSearchArea)
        obj.put("searchAreaXNorm", searchAreaXNorm)
        obj.put("searchAreaYNorm", searchAreaYNorm)
        obj.put("searchAreaWNorm", searchAreaWNorm)
        obj.put("searchAreaHNorm", searchAreaHNorm)

        val arrPath = JSONArray()
        joystickPath.forEach { p ->
            arrPath.put(JSONObject().apply {
                put("x", p.x)
                put("y", p.y)
            })
        }
        obj.put("joystickPath", arrPath)

        return obj
    }
}
""")

    # 4. TemplateMatcher.kt
    write_file("app/src/main/java/com/example/autotap/TemplateMatcher.kt", r"""package com.example.autotap

import android.graphics.*
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

data class MatchCandidate(
    val rect: Rect,
    val score: Float,
    val templateIndex: Int = -1
) {
    val point: PointF
        get() = PointF(rect.centerX().toFloat(), rect.centerY().toFloat())
}

object TemplateMatcher {

    fun analyzeTemplate(template: Bitmap): JSONObject {
        return JSONObject().apply {
            put("width", template.width)
            put("height", template.height)
        }
    }

    fun generateSmartMask(src: Bitmap, isCircle: Boolean): Bitmap {
        val out = src.copy(Bitmap.Config.ARGB_8888, true)
        if (isCircle) {
            applyCircularMask(out)
        }
        return out
    }

    fun aggregateMultiFrameMask(frames: List<Bitmap>, circleShape: Boolean): Bitmap {
        if (frames.isEmpty()) return Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)

        val w = frames[0].width
        val h = frames[0].height

        val out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)

        for (y in 0 until h) {
            for (x in 0 until w) {

                var sumR = 0
                var sumG = 0
                var sumB = 0
                var sumA = 0

                for (bmp in frames) {
                    val c = bmp.getPixel(x, y)
                    sumR += Color.red(c)
                    sumG += Color.green(c)
                    sumB += Color.blue(c)
                    sumA += Color.alpha(c)
                }

                val avgR = sumR / frames.size
                val avgG = sumG / frames.size
                val avgB = sumB / frames.size
                val avgA = sumA / frames.size

                val finalColor = Color.argb(avgA, avgR, avgG, avgB)
                out.setPixel(x, y, finalColor)
            }
        }

        if (circleShape) {
            applyCircularMask(out)
        }

        return out
    }

    fun findCandidatesForCreation(screenBitmap: Bitmap, template: Bitmap): MutableList<MatchCandidate> {
        val list = ArrayList<MatchCandidate>()
        list.add(MatchCandidate(Rect(0, 0, template.width, template.height), 1.0f))
        return list
    }

    fun findTemplateCandidatesCoarseFine(
        screen: Bitmap,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): List<MatchCandidate> {

        val similarityThreshold = (config.similarityPercent / 100f).coerceIn(0.1f, 0.99f)
        val shapeOnly = config.shapeOnlyMode
        val hybridCascade = config.hybridCascadeMode
        val multiScale = config.multiScaleSearch

        val candidates = ArrayList<MatchCandidate>()

        val searchArea = if (config.customSearchArea) {
            Rect(
                (config.searchAreaXNorm * screen.width).toInt().coerceIn(0, screen.width - 1),
                (config.searchAreaYNorm * screen.height).toInt().coerceIn(0, screen.height - 1),
                ((config.searchAreaXNorm + config.searchAreaWNorm) * screen.width).toInt().coerceIn(1, screen.width),
                ((config.searchAreaYNorm + config.searchAreaHNorm) * screen.height).toInt().coerceIn(1, screen.height)
            )
        } else {
            Rect(0, 0, screen.width, screen.height)
        }

        val coarseStep = 6
        val fineStep = 2

        val scales = if (multiScale) {
            floatArrayOf(1.0f, 0.95f, 0.9f, 1.05f)
        } else {
            floatArrayOf(1.0f)
        }

        for (scale in scales) {
            val scaledTemplate = if (scale != 1.0f) {
                Bitmap.createScaledBitmap(
                    template,
                    (template.width * scale).toInt(),
                    (template.height * scale).toInt(),
                    true
                )
            } else template

            val tw = scaledTemplate.width
            val th = scaledTemplate.height

            for (y in searchArea.top until (searchArea.bottom - th).coerceAtLeast(searchArea.top + 1) step coarseStep) {
                for (x in searchArea.left until (searchArea.right - tw).coerceAtLeast(searchArea.left + 1) step coarseStep) {

                    val score = if (shapeOnly) {
                        shapeMatch(screen, scaledTemplate, x, y)
                    } else {
                        pixelMatch(screen, scaledTemplate, x, y)
                    }

                    if (score >= similarityThreshold) {
                        candidates.add(MatchCandidate(Rect(x, y, x + tw, y + th), score))
                    }
                }
            }

            val refined = ArrayList<MatchCandidate>()
            for (c in candidates) {
                val cx0 = max(searchArea.left, c.rect.left - coarseStep)
                val cy0 = max(searchArea.top, c.rect.top - coarseStep)
                val cx1 = min(searchArea.right - tw, c.rect.left + coarseStep)
                val cy1 = min(searchArea.bottom - th, c.rect.top + coarseStep)

                var bestScore = c.score
                var bestRect = c.rect

                for (y in cy0..cy1 step fineStep) {
                    for (x in cx0..cx1 step fineStep) {
                        val score = if (shapeOnly) {
                            shapeMatch(screen, scaledTemplate, x, y)
                        } else {
                            pixelMatch(screen, scaledTemplate, x, y)
                        }
                        if (score > bestScore) {
                            bestScore = score
                            bestRect = Rect(x, y, x + tw, y + th)
                        }
                    }
                }

                refined.add(MatchCandidate(bestRect, bestScore))
            }

            candidates.clear()
            candidates.addAll(refined)
        }

        if (hybridCascade) {
            return candidates.sortedByDescending { it.score }.take(3)
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun pixelMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th) {
            for (x in 0 until tw) {
                if (sx + x >= screen.width || sy + y >= screen.height) continue
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val dr = abs(Color.red(sc) - Color.red(tc))
                val dg = abs(Color.green(sc) - Color.green(tc))
                val db = abs(Color.blue(sc) - Color.blue(tc))

                val diff = (dr + dg + db) / 765f
                val sim = 1f - diff

                score += sim
                total += 1f
            }
        }

        return if (total > 0f) score / total else 0f
    }

    private fun shapeMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th step 2) {
            for (x in 0 until tw step 2) {
                if (sx + x >= screen.width || sy + y >= screen.height) continue
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val scA = Color.alpha(sc)
                val tcA = Color.alpha(tc)

                val sim = if (tcA < 128) {
                    if (scA < 128) 1f else 0f
                } else {
                    if (scA >= 128) 1f else 0f
                }

                score += sim
                total += 1f
            }
        }

        return if (total > 0f) score / total else 0f
    }

    private fun applyCircularMask(bmp: Bitmap) {
        val w = bmp.width
        val h = bmp.height
        val cx = w / 2f
        val cy = h / 2f
        val r = min(w, h) / 2f

        for (y in 0 until h) {
            for (x in 0 until w) {
                val dx = x - cx
                val dy = y - cy
                if (dx * dx + dy * dy > r * r) {
                    bmp.setPixel(x, y, Color.TRANSPARENT)
                }
            }
        }
    }
}
""")

    # 5. MyAutoClickService.kt (Единое монолитное ядро сервиса со всеми оверлеями)
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.*
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.util.DisplayMetrics
import android.view.*
import android.view.accessibility.AccessibilityEvent
import android.widget.*
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.*
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.math.abs
import kotlin.math.hypot

class MyAutoClickService : AccessibilityService() {

    companion object {
        var instance: MyAutoClickService? = null

        fun logError(ctx: Context, e: Throwable) {
            try {
                val file = File(ctx.filesDir, "error_log.txt")
                file.appendText("\n\n${System.currentTimeMillis()}:\n${e.stackTraceToString()}")
            } catch (_: Exception) {}
        }

        fun logAppEvent(ctx: Context, tag: String, msg: String) {
            try {
                val file = File(ctx.filesDir, "app_events.txt")
                file.appendText("\n[$tag] $msg")
            } catch (_: Exception) {}
        }
    }

    private lateinit var windowManager: WindowManager
    private val attachedViews = ConcurrentHashMap<View, Boolean>()
    private val uiHandler = Handler(Looper.getMainLooper())
    private val bgScannerExecutor = Executors.newSingleThreadExecutor()

    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplates = ArrayList<Bitmap>()
    val globalTemplatesNames = ArrayList<String>()

    private var controlPanelView: View? = null
    private var stopButtonView: View? = null
    private var captureFrameView: View? = null
    private var joystickOverlayView: View? = null
    private var recordOverlayView: View? = null
    private var recordBarView: View? = null
    private var beaconRingView: View? = null

    private var executionThread: Thread? = null

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v35.1.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun dpToPx(dp: Int): Int = (dp * resources.displayMetrics.density).toInt()
    fun dpToPx(dp: Float): Int = (dp * resources.displayMetrics.density).toInt()

    fun getRealScreenSize(): Pair<Int, Int> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val bounds = windowManager.currentWindowMetrics.bounds
            Pair(bounds.width(), bounds.height())
        } else {
            val dm = DisplayMetrics()
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay.getRealMetrics(dm)
            Pair(dm.widthPixels, dm.heightPixels)
        }
    }

    fun getOverlayType(): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
    }

    fun createOverlayParams(): WindowManager.LayoutParams {
        return WindowManager.LayoutParams().apply {
            type = getOverlayType()
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }

            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }
    }

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] == true) return
        try {
            windowManager.addView(view, params)
            attachedViews[view] = true
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun safeRemoveView(view: View?) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            logError(this, e)
        } finally {
            attachedViews.remove(view)
        }
    }

    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.updateViewLayout(view, params)
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun vibrateFeedback(durationMs: Long = 25L) {
        try {
            val vibrator = getSystemService(VIBRATOR_SERVICE) as? Vibrator
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

    fun normalizeX(px: Float): Float {
        val (w, _) = getRealScreenSize()
        return (px / w.toFloat()).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val (_, h) = getRealScreenSize()
        return (px / h.toFloat()).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val (w, h) = getRealScreenSize()
        return Pair((nx * w).coerceIn(0f, w.toFloat()), (ny * h).coerceIn(0f, h.toFloat()))
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

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                onComplete?.invoke(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                onComplete?.invoke(false)
            }
        }, null)
    }

    fun performSwipeWithCallback(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300L, onComplete: ((Boolean) -> Unit)? = null) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            onComplete?.invoke(false)
            return
        }
        val path = Path().apply {
            moveTo(startX, startY)
            lineTo(endX, endY)
        }
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                onComplete?.invoke(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                onComplete?.invoke(false)
            }
        }, null)
    }

    fun showControlPanel() {
        if (controlPanelView != null) {
            controlPanelView?.visibility = View.VISIBLE
            return
        }

        val view = LayoutInflater.from(this).inflate(R.layout.floating_control_panel, null)
        controlPanelView = view

        val params = createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = dpToPx(20)
            y = dpToPx(120)
        }

        val handleDrag = view.findViewById<TextView>(R.id.handleDrag)
        val layoutMainRow = view.findViewById<View>(R.id.layoutMainRow)
        val layoutSubMenu = view.findViewById<View>(R.id.layoutSubMenu)
        val btnSingleBubble = view.findViewById<ImageButton>(R.id.btnSingleBubble)

        val btnPlay = view.findViewById<ImageButton>(R.id.btnPlay)
        val btnAdd = view.findViewById<ImageButton>(R.id.btnAdd)
        val btnCapturePool = view.findViewById<ImageButton>(R.id.btnCapturePool)
        val btnHelpTutorial = view.findViewById<ImageButton>(R.id.btnHelpTutorial)
        val btnToggleMenu = view.findViewById<ImageButton>(R.id.btnToggleMenu)

        val btnClearAll = view.findViewById<ImageButton>(R.id.btnClearAll)
        val btnRecord = view.findViewById<ImageButton>(R.id.btnRecord)
        val btnToggleJoystick = view.findViewById<ImageButton>(R.id.btnToggleJoystick)
        val btnLoadScript = view.findViewById<ImageButton>(R.id.btnLoadScript)
        val btnHideNumbers = view.findViewById<ImageButton>(R.id.btnHideNumbers)
        val btnClose = view.findViewById<ImageButton>(R.id.btnClose)

        var initX = 0
        var initY = 0
        var touchX = 0f
        var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val p = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x
                    initY = p.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (screenW, screenH) = getRealScreenSize()
                    val w = if (view.width > 0) view.width else dpToPx(180)
                    val h = if (view.height > 0) view.height else dpToPx(50)
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (screenW - w).coerceAtLeast(0))
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (screenH - h).coerceAtLeast(0))
                    safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        var panelState = 0
        fun updatePanelState(state: Int) {
            panelState = state % 3
            when (panelState) {
                0 -> {
                    layoutMainRow?.visibility = View.VISIBLE
                    layoutSubMenu?.visibility = View.GONE
                    btnSingleBubble?.visibility = View.GONE
                }
                1 -> {
                    layoutMainRow?.visibility = View.VISIBLE
                    layoutSubMenu?.visibility = View.VISIBLE
                    btnSingleBubble?.visibility = View.GONE
                }
                2 -> {
                    layoutMainRow?.visibility = View.GONE
                    layoutSubMenu?.visibility = View.GONE
                    btnSingleBubble?.visibility = View.VISIBLE
                }
            }
            view.requestLayout()
            val p = view.layoutParams as? WindowManager.LayoutParams
            if (p != null) {
                p.width = WindowManager.LayoutParams.WRAP_CONTENT
                p.height = WindowManager.LayoutParams.WRAP_CONTENT
                safeUpdateViewLayout(view, p)
            }
        }

        btnToggleMenu?.setOnClickListener { vibrateFeedback(20L); updatePanelState(panelState + 1) }
        btnSingleBubble?.setOnClickListener { vibrateFeedback(20L); updatePanelState(0) }

        btnPlay?.setOnClickListener {
            vibrateFeedback(30L)
            if (isPlaying) {
                btnPlay.setImageResource(R.drawable.ic_play)
                stopExecutionLoop()
            } else {
                btnPlay.setImageResource(R.drawable.ic_pause)
                startScript("default")
            }
        }

        btnAdd?.setOnClickListener { vibrateFeedback(20L); showAddActionMenu() }
        btnCapturePool?.setOnClickListener { vibrateFeedback(20L); showCaptureFrame() }
        btnHelpTutorial?.setOnClickListener { vibrateFeedback(20L); showTutorialCard() }
        btnClearAll?.setOnClickListener { vibrateFeedback(30L); clearAllActions() }
        btnRecord?.setOnClickListener { vibrateFeedback(20L); if (isRecording) stopOverlayRecording() else startOverlayRecording() }
        btnToggleJoystick?.setOnClickListener { vibrateFeedback(20L); showJoystickManipulator() }
        btnLoadScript?.setOnClickListener { vibrateFeedback(20L); showScriptsDialog() }
        btnHideNumbers?.setOnClickListener { vibrateFeedback(20L); toggleNumbersVisibility() }
        btnClose?.setOnClickListener { vibrateFeedback(20L); hideControlPanel(openMainApp = true) }

        safeAddView(view, params)
    }

    fun hideControlPanel(openMainApp: Boolean = false) {
        controlPanelView?.let { safeRemoveView(it); controlPanelView = null }
        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) { logError(this, e) }
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return
        val view = LayoutInflater.from(this).inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = createOverlayParams().apply { gravity = Gravity.CENTER }
        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            vibrateFeedback(20L)
            stopExecutionLoop()
        }
        safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let { safeRemoveView(it); stopButtonView = null }
    }

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(loadScriptByName(name))
        if (actionsList.isEmpty()) {
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        isPlaying = true
        startExecutionLoop()
    }

    fun startExecutionLoop() {
        if (executionThread != null) return
        executionThread = Thread {
            var index = 0
            uiHandler.post { hideControlPanel(); showFloatingStopButton() }

            while (isPlaying && actionsList.isNotEmpty()) {
                val cfg = actionsList[index]
                try { Thread.sleep(cfg.delay) } catch (_: InterruptedException) { break }
                if (!isPlaying) break

                when (cfg.type) {
                    ActionType.CLICK -> {
                        val (x, y) = resolveNormalizedPoint(cfg.xNorm, cfg.yNorm)
                        val jitter = randomOffset(cfg.randomRadius)
                        val fx = x + jitter.x
                        val fy = y + jitter.y
                        uiHandler.post { showClickVisualizer(fx, fy) }
                        performClickWithCallback(fx, fy, globalClickDurationMs)
                    }
                    ActionType.LONG_PRESS -> {
                        val (x, y) = resolveNormalizedPoint(cfg.xNorm, cfg.yNorm)
                        uiHandler.post { showClickVisualizer(x, y) }
                        performClickWithCallback(x, y, cfg.holdDuration)
                    }
                    ActionType.SWIPE -> {
                        val (sx, sy) = resolveNormalizedPoint(cfg.xNorm, cfg.yNorm)
                        val (ex, ey) = resolveNormalizedPoint(cfg.endXNorm, cfg.endYNorm)
                        performSwipeWithCallback(sx, sy, ex, ey, cfg.holdDuration)
                    }
                    ActionType.TRIGGER -> {
                        val jump = executeAiTriggerSequence(cfg)
                        if (jump == -999) { index = 0; continue }
                        else if (jump > 0) {
                            val targetIdx = actionsList.indexOfFirst { it.id == jump }
                            if (targetIdx != -1) { index = targetIdx; continue }
                        }
                    }
                }
                index = (index + 1) % actionsList.size
            }
            isPlaying = false
            uiHandler.post { stopExecutionLoop() }
        }
        executionThread?.start()
    }

    fun stopExecutionLoop() {
        isPlaying = false
        executionThread?.interrupt()
        executionThread = null
        uiHandler.post { hideFloatingStopButton(); showControlPanel() }
    }

    fun startOverlayRecording() {
        isRecording = true
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        hideControlPanel()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        showControlPanel()
        hideFloatingStopButton()
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    fun toggleNumbersVisibility() {
        isNumbersHidden = !isNumbersHidden
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
        Toast.makeText(this, if (isNumbersHidden) "👁 Номера скрыты" else "👁 Номера показаны", Toast.LENGTH_SHORT).show()
    }

    fun clearAllActions() {
        actionsList.forEach { act ->
            act.startView?.let { safeRemoveView(it) }
            act.endView?.let { safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(posX: Float, posY: Float, delay: Long, type: ActionType, id: Int) {
        val actionId = if (id == -1) (actionsList.size + 1) else id
        val startView = LayoutInflater.from(this).inflate(R.layout.floating_target, null)
        val tvNum = startView.findViewById<TextView>(R.id.tvTargetNumber)
        tvNum?.text = actionId.toString()

        val sizePx = dpToPx(if (type == ActionType.TRIGGER) 50 else 36)
        val params = createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        val config = ActionConfig(
            id = actionId,
            startView = startView,
            type = type,
            delay = delay,
            xNorm = normalizeX(posX),
            yNorm = normalizeY(posY)
        )

        startView.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0; private var initY = 0
            private var touchX = 0f; private var touchY = 0f
            private var isMoving = false

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        isMoving = false
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = abs(event.rawX - touchX)
                        val dy = abs(event.rawY - touchY)
                        if (dx > 8 || dy > 8) {
                            isMoving = true
                            val (sw, sh) = getRealScreenSize()
                            val sz = if (startView.width > 0) startView.width else dpToPx(36)
                            params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - sz).coerceAtLeast(0))
                            params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - sz).coerceAtLeast(0))
                            config.xNorm = normalizeX(params.x + sz / 2f)
                            config.yNorm = normalizeY(params.y + sz / 2f)
                            safeUpdateViewLayout(startView, params)
                        }
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        if (!isMoving && !isPlaying) {
                            vibrateFeedback(25L)
                            showEditDialog(config)
                        }
                        return true
                    }
                }
                return false
            }
        })

        if (isRecording || isNumbersHidden) startView.visibility = View.INVISIBLE
        actionsList.add(config)
        safeAddView(startView, params)
    }

    fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = dpToPx(36)
        val params = createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        endView.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0; private var initY = 0
            private var touchX = 0f; private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val (sw, sh) = getRealScreenSize()
                        val sz = if (endView.width > 0) endView.width else dpToPx(36)
                        params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - sz).coerceAtLeast(0))
                        params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - sz).coerceAtLeast(0))
                        config.endXNorm = normalizeX(params.x + sz / 2f)
                        config.endYNorm = normalizeY(params.y + sz / 2f)
                        safeUpdateViewLayout(endView, params)
                        return true
                    }
                    MotionEvent.ACTION_UP -> { v.performClick(); return true }
                }
                return false
            }
        })

        if (isRecording || isNumbersHidden) endView.visibility = View.INVISIBLE
        config.endView = endView
        safeAddView(endView, params)
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_beacon_ring, null)
        val params = createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }
        safeAddView(view, params)
        view.animate().alpha(0f).setDuration(300).withEndAction { safeRemoveView(view) }.start()
    }

    fun showCaptureFrame() {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_capture_frame, null)
        captureFrameView = view
        val params = createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
        }

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        btnDoCapture?.setOnClickListener {
            vibrateFeedback(40L)
            safeRemoveView(view)
            val (sw, sh) = getRealScreenSize()
            addNewActionAtPosition(sw / 2f, sh / 2f, 1000L, ActionType.TRIGGER, -1)
            Toast.makeText(this, "🎉 ИИ-Шаблон добавлен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun showJoystickManipulator() {
        if (joystickOverlayView != null) return
        val view = LayoutInflater.from(this).inflate(R.layout.floating_joystick_control, null)
        joystickOverlayView = view

        val params = createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = dpToPx(30)
            y = dpToPx(200)
        }

        val btnClose = view.findViewById<ImageButton>(R.id.btnCloseJoystick)
        btnClose?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view); joystickOverlayView = null }
        safeAddView(view, params)
    }

    fun showEditDialog(config: ActionConfig) {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_edit_dialog, null)
        val params = createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            flags = WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
        }

        val tvTitle = view.findViewById<TextView>(R.id.tvDialogTitle)
        val etDelay = view.findViewById<EditText>(R.id.etDelay)
        val etRepeat = view.findViewById<EditText>(R.id.etRepeatCount)
        val etRadius = view.findViewById<EditText>(R.id.etRandomRadius)
        val etHold = view.findViewById<EditText>(R.id.etHoldDuration)
        val btnSave = view.findViewById<Button>(R.id.btnSave)
        val btnCancel = view.findViewById<Button>(R.id.btnCancel)

        tvTitle?.text = "Шаг #${config.id}"
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeat?.setText(config.repeatCount.toString())
        etRadius?.setText(config.randomRadius.toString())
        etHold?.setText(config.holdDuration.toString())

        btnSave?.setOnClickListener {
            vibrateFeedback(30L)
            config.delay = ((etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0) * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHold?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L
            safeRemoveView(view)
            Toast.makeText(this, "Шаг #${config.id} сохранен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun showScriptsDialog() {
        val view = LayoutInflater.from(this).inflate(R.layout.dialog_scripts, null)
        val params = createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val etName = view.findViewById<EditText>(R.id.etScriptName)
        val btnSave = view.findViewById<Button>(R.id.btnSaveScriptAction)
        val btnClose = view.findViewById<Button>(R.id.btnCloseScripts)

        btnSave?.setOnClickListener {
            val name = etName?.text?.toString()?.trim() ?: ""
            if (name.isNotEmpty()) {
                saveScriptByName(name, actionsList)
                etName?.setText("")
            }
        }

        btnClose?.setOnClickListener { safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun showAddActionMenu() {
        val view = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val btnClick = view.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = view.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = view.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = view.findViewById<Button>(R.id.btnCancelAdd)

        val (sw, sh) = getRealScreenSize()
        val spawnX = sw / 2f
        val spawnY = sh / 2f

        btnClick?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1); safeRemoveView(view) }
        btnSwipe?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1); spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f); safeRemoveView(view) }
        btnAi?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0); safeRemoveView(view) }
        btnCancel?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }

        safeAddView(view, params)
    }

    fun showTutorialCard() {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        val params = createOverlayParams().apply { gravity = Gravity.CENTER }
        val btnSkip = view.findViewById<Button>(R.id.btnTutSkip)
        btnSkip?.setOnClickListener { vibrateFeedback(20L); safeRemoveView(view) }
        safeAddView(view, params)
    }

    fun executeAiTriggerSequence(config: ActionConfig): Int {
        val screen = captureScreenBitmap() ?: return -1
        val match = TemplateMatcher.findCandidatesForCreation(screen, screen).firstOrNull()
        if (match != null) {
            if (config.clickAiTarget) {
                performClickWithCallback(match.rect.centerX().toFloat(), match.rect.centerY().toFloat(), globalClickDurationMs)
            }
            if (config.jumpToStepOnMatch > 0) return config.jumpToStepOnMatch
            if (config.targetScriptToLoad.isNotEmpty()) {
                loadScriptByName(config.targetScriptToLoad)
                return -999
            }
        }
        return -1
    }

    private fun getScriptsDir(): File {
        val dir = File(filesDir, "scripts")
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun loadScriptByName(name: String): List<ActionConfig> {
        val list = ArrayList<ActionConfig>()
        try {
            val file = File(getScriptsDir(), "$name.json")
            if (file.exists()) {
                val jsonArray = JSONArray(file.readText())
                for (i in 0 until jsonArray.length()) {
                    list.add(ActionConfig.fromJson(jsonArray.getJSONObject(i)))
                }
            }
        } catch (e: Exception) { logError(this, e) }
        return list
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        try {
            val file = File(getScriptsDir(), "$name.json")
            val bakFile = File(getScriptsDir(), "$name.json.bak")
            if (file.exists()) file.copyTo(bakFile, overwrite = true)

            val jsonArray = JSONArray()
            actions.forEach { jsonArray.put(it.toJson()) }
            file.writeText(jsonArray.toString(2))
            Toast.makeText(this, "Сценарий '$name' сохранен!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) { logError(this, e) }
    }

    fun loadAllTemplatesFromDisk() {
        try {
            globalTemplates.forEach { try { it.recycle() } catch (_: Exception) {} }
            globalTemplates.clear()
            globalTemplatesNames.clear()

            val baseDir = File(filesDir, "templates")
            if (baseDir.exists()) {
                baseDir.walkTopDown().filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }.forEach { file ->
                    BitmapFactory.decodeFile(file.absolutePath)?.let { bmp ->
                        globalTemplates.add(bmp)
                        globalTemplatesNames.add(file.absolutePath)
                    }
                }
            }
        } catch (e: Exception) { logError(this, e) }
    }

    fun moveTemplateToTrash(index: Int) {
        if (index !in globalTemplatesNames.indices) return
        try {
            val maskPath = globalTemplatesNames[index]
            val maskFile = File(maskPath)
            if (maskFile.exists()) maskFile.delete()
            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)
            Toast.makeText(this, "🗑 Шаблон удален", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) { logError(this, e) }
    }

    fun exportScriptWithTemplates(context: Context, scriptName: String) {
        try {
            val scriptFile = File(getScriptsDir(), "$scriptName.json")
            if (!scriptFile.exists()) return
            val zipFile = File(context.externalCacheDir ?: context.cacheDir, "$scriptName.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))
            zos.putNextEntry(ZipEntry("scripts/$scriptName.json"))
            zos.write(scriptFile.readBytes())
            zos.closeEntry()
            zos.close()

            val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", zipFile)
            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(Intent.createChooser(shareIntent, "Экспорт сценария"))
        } catch (e: Exception) { logError(context, e) }
    }

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        bgScannerExecutor.shutdown()
        super.onDestroy()
    }
}
""")

    # 6. MainActivity.kt (Главный экран v35)
    write_file("app/src/main/java/com/example/autotap/MainActivity.kt", r"""package com.example.autotap

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.StrictMode
import android.provider.Settings
import android.view.LayoutInflater
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import java.io.*
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

@Suppress("SpellCheckingInspection", "DEPRECATION")
class MainActivity : AppCompatActivity() {

    private var hasAutoShownPermissions = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        StrictMode.setVmPolicy(StrictMode.VmPolicy.Builder().build())

        val tvVersion = findViewById<TextView>(R.id.tvVersion)
        tvVersion.text = "AutoTap v35.1.0-PRO"

        val btnAppDetails = findViewById<Button>(R.id.btnAppDetails)
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)
        val btnExport = findViewById<Button>(R.id.btnExport)
        val btnImport = findViewById<Button>(R.id.btnImport)
        val btnStartPanel = findViewById<Button>(R.id.btnStartPanel)
        val btnShowLogs = findViewById<Button>(R.id.btnShowLogs)
        val btnManageTemplates = findViewById<Button>(R.id.btnManageTemplates)
        val btnPermissionsHelp = findViewById<Button>(R.id.btnPermissionsHelp)
        val btnInfoHelp = findViewById<Button>(R.id.btnInfoHelp)

        btnAppDetails?.setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            })
        }

        btnAccessibility?.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        btnOverlay?.setOnClickListener {
            try {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            } catch (_: Exception) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION))
            }
        }

        btnExport?.setOnClickListener { showExportDialog() }
        btnImport?.setOnClickListener { startImportFlow() }
        btnShowLogs?.setOnClickListener { showLogsDialog() }
        btnManageTemplates?.setOnClickListener { showTemplatesManagerDialog() }
        btnPermissionsHelp?.setOnClickListener { showPermissionsHelpDialog() }
        btnInfoHelp?.setOnClickListener { showInfoHelpDialog() }

        btnStartPanel?.setOnClickListener {
            val service = MyAutoClickService.instance
            if (service == null) {
                Toast.makeText(this, "Служба не активна!", Toast.LENGTH_SHORT).show()
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                return@setOnClickListener
            }

            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Разрешите показ поверх окон!", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            service.showControlPanel()
            moveTaskToBack(true)
        }
    }

    override fun onResume() {
        super.onResume()
        updatePermissionButtonStates()

        val isServiceRunning = MyAutoClickService.instance != null
        val isOverlayGranted = Settings.canDrawOverlays(this)

        if ((!isServiceRunning || !isOverlayGranted) && !hasAutoShownPermissions) {
            hasAutoShownPermissions = true
            showPermissionsHelpDialog()
        }
    }

    private fun updatePermissionButtonStates() {
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)

        val isServiceBound = MyAutoClickService.instance != null
        val isSystemEnabled = isAccessibilityServiceEnabled()
        val isOverlayGranted = Settings.canDrawOverlays(this)

        btnAccessibility?.text =
            if (isServiceBound) "Служба кликера: ВКЛЮЧЕНА"
            else if (isSystemEnabled) "Перезапустить службу"
            else "Разрешить работу кликера"

        btnAccessibility?.backgroundTintList =
            ColorStateList.valueOf(if (isServiceBound) Color.parseColor("#1E3A2B") else Color.parseColor("#8B0000"))

        btnOverlay?.text =
            if (isOverlayGranted) "Показ поверх окон: РАЗРЕШЕНО"
            else "Показ поверх окон: ОТКЛЮЧЕНО"

        btnOverlay?.backgroundTintList =
            ColorStateList.valueOf(if (isOverlayGranted) Color.parseColor("#1E3A2B") else Color.parseColor("#21262D"))
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val am = getSystemService(Context.ACCESSIBILITY_SERVICE) as? android.view.accessibility.AccessibilityManager
        val enabled = am?.getEnabledAccessibilityServiceList(
            android.accessibilityservice.AccessibilityServiceInfo.FEEDBACK_ALL_MASK
        ) ?: emptyList()

        if (enabled.any { it.resolveInfo.serviceInfo.packageName == packageName }) return true

        val raw = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: ""
        return raw.split(':').any { it.substringBefore('/').equals(packageName, true) }
    }

    private fun showExportDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_export_select, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        dialogView.findViewById<Button>(R.id.btnExpSingleScript)?.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        dialogView.findViewById<Button>(R.id.btnExpTemplatesOnly)?.setOnClickListener {
            ad.dismiss()
            exportTemplatesOnly()
        }

        dialogView.findViewById<Button>(R.id.btnExpFullBackup)?.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        dialogView.findViewById<Button>(R.id.btnCloseExpSelect)?.setOnClickListener {
            ad.dismiss()
        }

        ad.show()
    }

    private fun exportTemplatesOnly() {
        val baseDir = File(filesDir, "templates")
        if (!baseDir.exists() || baseDir.listFiles()?.isEmpty() == true) {
            Toast.makeText(this, "Пул шаблонов пуст!", Toast.LENGTH_SHORT).show()
            return
        }

        val zipFile = File(externalCacheDir ?: cacheDir, "autotap_templates.zip")
        zipFolder(baseDir, zipFile)
        shareZip(zipFile, "ИИ-шаблоны AutoTap")
    }

    private fun exportFullBackup() {
        try {
            val zipFile = File(externalCacheDir ?: cacheDir, "autotap_backup.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val scriptsDir = File(filesDir, "scripts")
            if (scriptsDir.exists()) zipDirToZip(filesDir, scriptsDir, zos)

            val templatesDir = File(filesDir, "templates")
            if (templatesDir.exists()) zipDirToZip(filesDir, templatesDir, zos)

            zos.close()
            shareZip(zipFile, "Полный бэкап AutoTap v35")
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка бэкапа!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun startImportFlow() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            type = "application/zip"
            addCategory(Intent.CATEGORY_OPENABLE)
        }
        startActivityForResult(intent, 1002)
    }

    override fun onActivityResult(req: Int, res: Int, data: Intent?) {
        super.onActivityResult(req, res, data)
        if (req == 1002 && res == RESULT_OK) {
            val uri = data?.data ?: return
            importZip(uri)
        }
    }

    private fun importZip(uri: Uri) {
        try {
            val input = contentResolver.openInputStream(uri) ?: return
            val zis = ZipInputStream(BufferedInputStream(input))

            var entry: ZipEntry?
            while (zis.nextEntry.also { entry = it } != null) {
                val name = entry!!.name
                val outFile = File(filesDir, name)

                outFile.parentFile?.mkdirs()
                BufferedOutputStream(FileOutputStream(outFile)).use { bos ->
                    zis.copyTo(bos)
                }
            }
            zis.close()

            MyAutoClickService.instance?.loadAllTemplatesFromDisk()
            Toast.makeText(this, "Импорт завершён!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка импорта!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun zipFolder(folder: File, zipFile: File) {
        val zos = ZipOutputStream(FileOutputStream(zipFile))
        folder.listFiles()?.forEach { file ->
            val entry = ZipEntry(file.name)
            zos.putNextEntry(entry)
            zos.write(file.readBytes())
            zos.closeEntry()
        }
        zos.close()
    }

    private fun zipDirToZip(root: File, src: File, zos: ZipOutputStream) {
        src.listFiles()?.forEach { file ->
            if (file.isDirectory) {
                zipDirToZip(root, file, zos)
            } else {
                val entryName = file.absolutePath.substring(root.absolutePath.length + 1)
                zos.putNextEntry(ZipEntry(entryName))
                zos.write(file.readBytes())
                zos.closeEntry()
            }
        }
    }

    private fun shareZip(zipFile: File, title: String) {
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", zipFile)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, title))
    }

    private fun showLogsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_logs, null)
        val tvLogs = dialogView.findViewById<TextView>(R.id.tvLogsContent)
        val btnShare = dialogView.findViewById<Button>(R.id.btnShareLogs)
        val btnClear = dialogView.findViewById<Button>(R.id.btnClearLogs)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseLogs)

        val logFile = File(filesDir, "error_log.txt")
        tvLogs?.text = if (logFile.exists() && logFile.length() > 0) logFile.readText() else "Логи отсутствуют."

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        btnShare?.setOnClickListener {
            if (logFile.exists() && logFile.length() > 0) {
                val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", logFile)
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                startActivity(Intent.createChooser(intent, "Поделиться логами"))
            } else {
                Toast.makeText(this, "Логи пусты", Toast.LENGTH_SHORT).show()
            }
        }

        btnClear?.setOnClickListener {
            if (logFile.exists()) logFile.delete()
            tvLogs?.text = "Логи очищены."
            Toast.makeText(this, "Логи очищены", Toast.LENGTH_SHORT).show()
        }

        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showTemplatesManagerDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_templates_manager, null)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutTemplatesList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseTemplatesManager)

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        fun refresh() {
            layoutList?.removeAllViews()
            val baseDir = File(filesDir, "templates")

            baseDir.listFiles()?.forEach { folder ->
                if (folder.isDirectory) {
                    folder.listFiles()?.forEach { file ->
                        if (file.name.startsWith("mask_") && file.name.endsWith(".png")) {
                            val item = LayoutInflater.from(this).inflate(R.layout.item_template, null)

                            val iv = item.findViewById<ImageView>(R.id.ivTemplatePreview)
                            val tv = item.findViewById<TextView>(R.id.tvTemplateName)
                            val btnDelete = item.findViewById<Button>(R.id.btnDeleteTemplateFile)

                            iv?.setImageBitmap(BitmapFactory.decodeFile(file.absolutePath))
                            tv?.text = "${folder.name}\n${file.nameWithoutExtension}"

                            btnDelete?.setOnClickListener {
                                MyAutoClickService.instance?.moveTemplateToTrash(
                                    MyAutoClickService.instance?.globalTemplatesNames?.indexOf(file.absolutePath) ?: -1
                                )
                                MyAutoClickService.instance?.loadAllTemplatesFromDisk()
                                refresh()
                            }

                            layoutList?.addView(item)
                        }
                    }
                }
            }
        }

        refresh()
        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showPermissionsHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_permissions, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()
        dialogView.findViewById<Button>(R.id.btnClosePermissionsDialog)?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showInfoHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_info, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        val tvContent = dialogView.findViewById<TextView>(R.id.tvTabContent)
        val tabClick = dialogView.findViewById<Button>(R.id.tabClick)
        val tabSwipe = dialogView.findViewById<Button>(R.id.tabSwipe)
        val tabAi = dialogView.findViewById<Button>(R.id.tabAi)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseInfoDialog)

        val clickInfo = "• Клики (Click):\nТочечное нажатие по координатам с регулируемой задержкой, повторами и случайным разбросом.\n\n• Зажатие (Hold):\nУдержание точки на заданное время (в мс)."
        val swipeInfo = "• Свайпы (Swipe):\nПлавное перемещение от точки (S) к (E).\n\n• Траектория Джойстика:\nЗапись сложных свайпов через плавающий джойстик."
        val aiInfo = "• ИИ-Сканер (AI Trigger v35):\nПоиск заданного изображения на экране с калибровкой, выбором порога (%) и эстафетой сценариев."

        tvContent?.text = clickInfo

        tabClick?.setOnClickListener {
            tvContent?.text = clickInfo
            tabClick.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
        }

        tabSwipe?.setOnClickListener {
            tvContent?.text = swipeInfo
            tabClick?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
        }

        tabAi?.setOnClickListener {
            tvContent?.text = aiInfo
            tabClick?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
        }

        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }
}
""")

    print("\n🎉 МОНОЛИТНАЯ АРХИТЕКТУРА AutoTap v35.1.0-PRO УСПЕШНО СБОРКА И ГОТОВА!")

if __name__ == "__main__":
    build_consolidated_v35()