import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан модуль 360-Guard: {rel_path}")

def run_total_360_audit_patch():
    print("🚀 Запуск тотального 360-градусного патча AutoTap v37.1.0-PRO Enterprise...")

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
        versionCode = 2540
        versionName = "37.1.0-PRO"

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

    # 2. ActionType.kt
    action_type_code = r"""package com.example.autotap

enum class ActionType {
    CLICK,
    LONG_PRESS,
    SWIPE,
    SWIPE_PATH,
    TRIGGER,
    WAIT,
    LOOP,
    HOLD
}
"""
    write_file("app/src/main/java/com/example/autotap/ActionType.kt", action_type_code)

    # 3. ActionConfig.kt
    action_config_code = r"""package com.example.autotap

import android.graphics.PointF
import android.graphics.Rect
import android.view.View
import com.example.autotap.data.TemplateMetadata
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

    var waitType: String = "TIME",
    var loopType: String = "COUNT",
    var loopStartIndex: Int = 0,
    var loopCount: Int = 1,

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
    var exactMatchOnly: Boolean = false,
    var bestMatchAuto: Boolean = true,
    var semiTransparentMode: Boolean = false,
    var showSearchVisualizer: Boolean = true,
    var shapeOnlyMode: Boolean = false,
    var hybridCascadeMode: Boolean = true,
    var multiScaleSearch: Boolean = false,
    var autoTuningMode: Boolean = false,

    var customSearchArea: Boolean = false,
    var searchAreaXNorm: Float = 0f,
    var searchAreaYNorm: Float = 0f,
    var searchAreaWNorm: Float = 1f,
    var searchAreaHNorm: Float = 1f,

    var joystickPath: ArrayList<PointF> = ArrayList(),
    var calibratedRectNorm: Rect? = null,
    var templateMetadata: TemplateMetadata? = null,

    var dpi: Int = 480,
    var scaleFactor: Float = 1.0f,
    var version: Int = 35,
    var createdAt: Long = System.currentTimeMillis(),
    var updatedAt: Long = System.currentTimeMillis(),

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

            cfg.waitType = obj.optString("waitType", "TIME")
            cfg.loopType = obj.optString("loopType", "COUNT")
            cfg.loopStartIndex = obj.optInt("loopStartIndex", 0)
            cfg.loopCount = obj.optInt("loopCount", 1)

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
            cfg.exactMatchOnly = obj.optBoolean("exactMatchOnly", false)
            cfg.bestMatchAuto = obj.optBoolean("bestMatchAuto", true)
            cfg.semiTransparentMode = obj.optBoolean("semiTransparentMode", false)
            cfg.showSearchVisualizer = obj.optBoolean("showSearchVisualizer", true)
            cfg.shapeOnlyMode = obj.optBoolean("shapeOnlyMode", false)
            cfg.hybridCascadeMode = obj.optBoolean("hybridCascadeMode", true)
            cfg.multiScaleSearch = obj.optBoolean("multiScaleSearch", false)
            cfg.autoTuningMode = obj.optBoolean("autoTuningMode", false)

            cfg.customSearchArea = obj.optBoolean("customSearchArea", false)
            cfg.searchAreaXNorm = obj.optDouble("searchAreaXNorm", 0.0).toFloat()
            cfg.searchAreaYNorm = obj.optDouble("searchAreaYNorm", 0.0).toFloat()
            cfg.searchAreaWNorm = obj.optDouble("searchAreaWNorm", 1.0).toFloat()
            cfg.searchAreaHNorm = obj.optDouble("searchAreaHNorm", 1.0).toFloat()

            cfg.dpi = obj.optInt("dpi", 480)
            cfg.scaleFactor = obj.optDouble("scaleFactor", 1.0).toFloat()
            cfg.version = obj.optInt("version", 35)
            cfg.createdAt = obj.optLong("createdAt", System.currentTimeMillis())
            cfg.updatedAt = obj.optLong("updatedAt", System.currentTimeMillis())

            if (obj.has("templateMetadata")) {
                cfg.templateMetadata = TemplateMetadata.fromJson(obj.getJSONObject("templateMetadata"))
            }

            val arrPath = obj.optJSONArray("joystickPath") ?: JSONArray()
            cfg.joystickPath = ArrayList<PointF>().apply {
                for (i in 0 until arrPath.length()) {
                    val p = arrPath.optJSONObject(i)
                    add(PointF(p.optDouble("x", 0.0).toFloat(), p.optDouble("y", 0.0).toFloat()))
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
        obj.put("waitType", waitType)
        obj.put("loopType", loopType)
        obj.put("loopStartIndex", loopStartIndex)
        obj.put("loopCount", loopCount)
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
        obj.put("exactMatchOnly", exactMatchOnly)
        obj.put("bestMatchAuto", bestMatchAuto)
        obj.put("semiTransparentMode", semiTransparentMode)
        obj.put("showSearchVisualizer", showSearchVisualizer)
        obj.put("shapeOnlyMode", shapeOnlyMode)
        obj.put("hybridCascadeMode", hybridCascadeMode)
        obj.put("multiScaleSearch", multiScaleSearch)
        obj.put("autoTuningMode", autoTuningMode)
        obj.put("customSearchArea", customSearchArea)
        obj.put("searchAreaXNorm", searchAreaXNorm)
        obj.put("searchAreaYNorm", searchAreaYNorm)
        obj.put("searchAreaWNorm", searchAreaWNorm)
        obj.put("searchAreaHNorm", searchAreaHNorm)
        obj.put("dpi", dpi)
        obj.put("scaleFactor", scaleFactor.toDouble())
        obj.put("version", version)
        obj.put("createdAt", createdAt)
        obj.put("updatedAt", System.currentTimeMillis())

        templateMetadata?.let { obj.put("templateMetadata", it.toJson()) }

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
"""
    write_file("app/src/main/java/com/example/autotap/ActionConfig.kt", action_config_code)

    # 4. GestureExecutor.kt
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
import com.example.autotap.MyAutoClickService
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
                MyAutoClickService.logAppEvent(service, "GESTURE", "❌ Ошибка: API Android < 24 не поддерживает жесты")
                onComplete?.invoke(false)
                finishGestureTask()
                return@Runnable
            }

            MyAutoClickService.logAppEvent(service, "GESTURE", "📤 Отправка клика в ОС: pos=($x, $y) | duration=${duration}ms")

            val path = Path().apply { moveTo(x, y) }
            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            val res = service.dispatchGesture(gesture, object : AccessibilityService.GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "✅ Клик выполнен ОС Android: ($x, $y)")
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "⚠️ Клик отменен ОС Android: ($x, $y)")
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                MyAutoClickService.logAppEvent(service, "GESTURE", "❌ dispatchGesture вернул false для клика ($x, $y)")
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
            val pointCount = if (smoothed.isNotEmpty()) smoothed.size else 2
            MyAutoClickService.logAppEvent(service, "GESTURE", "📤 Отправка свайпа в ОС: ($startX, $startY) -> ($endX, $endY) | точек=$pointCount | duration=${duration}ms")

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
                    MyAutoClickService.logAppEvent(service, "GESTURE", "✅ Свайп выполнен ОС Android")
                    onComplete?.invoke(true)
                    finishGestureTask()
                }
                override fun onCancelled(gestureDescription: GestureDescription?) {
                    MyAutoClickService.logAppEvent(service, "GESTURE", "⚠️ Свайп отменен ОС Android")
                    onComplete?.invoke(false)
                    finishGestureTask()
                }
            }, null)

            if (!res) {
                MyAutoClickService.logAppEvent(service, "GESTURE", "❌ dispatchGesture вернул false для свайпа")
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

    # 5. MyAutoClickService.kt (Явные полные имена android.graphics.Color)
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.accessibilityservice.GestureDescription
import android.animation.ObjectAnimator
import android.animation.PropertyValuesHolder
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.PointF
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Typeface
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.FileProvider
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScenarioRunner
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ClickVisualizerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.ScriptsDialog
import java.io.File
import java.io.FileOutputStream
import java.io.PrintWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.math.abs

class MyAutoClickService : AccessibilityService() {

    companion object {
        var instance: MyAutoClickService? = null
        private val logLock = Any()

        @JvmStatic
        fun logError(ctx: Context, e: Throwable) {
            android.util.Log.e("AutoTap", "Caught Exception", e)
            synchronized(logLock) {
                try {
                    val logFile = File(ctx.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("=== [${sdf.format(Date())}] [ERROR] ===")
                        e.printStackTrace(writer)
                        writer.println()
                        writer.flush()
                    }
                } catch (_: Exception) {}
            }
        }

        @JvmStatic
        fun logAppEvent(ctx: Context, tag: String, msg: String) {
            android.util.Log.d("AutoTap", "[$tag] $msg")
            synchronized(logLock) {
                try {
                    val logFile = File(ctx.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("[${sdf.format(Date())}] [$tag] $msg")
                        writer.flush()
                    }
                } catch (_: Exception) {}
            }
        }
    }

    // --- CORE SUBSYSTEMS ---
    lateinit var overlayManager: OverlayManager
    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var scenarioRunner: ScenarioRunner
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // --- UI OVERLAYS ---
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay
    lateinit var clickVisualizerOverlay: ClickVisualizerOverlay

    // --- TUTORIAL STATE ---
    private var tutorialCardView: View? = null
    private var currentTutorialStep = 0
    private var isTutorialActive = false
    private var highlightedButtonAnim: ObjectAnimator? = null

    // --- STATE ---
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplates: ArrayList<Bitmap>
        get() = templateRepository.globalTemplates

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    private val uiHandler = Handler(Looper.getMainLooper())

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        templateRepository = TemplateRepository.init(this)
        scriptRepository = ScriptRepository.init(this)

        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        scenarioRunner = ScenarioRunner(this)
        aiScannerEngine = AiScannerEngine(this)

        controlPanelOverlay = ControlPanelOverlay(this)
        joystickOverlay = JoystickOverlay(this)
        captureFrameOverlay = CaptureFrameOverlay(this)
        debuggerOverlay = ScenarioDebuggerOverlay(this)
        clickVisualizerOverlay = ClickVisualizerOverlay(this)

        templateRepository.loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        logAppEvent(this, "SERVICE", "🚀 Служба AutoTap v37.1.0-PRO запущен")
        Toast.makeText(this, "AutoTap v37.1.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun vibrateFeedback(ms: Long = 25L) = gestureExecutor.vibrateFeedback(ms)

    fun getRealScreenSize(): Pair<Int, Int> = overlayManager.getRealScreenSize()
    fun dpToPx(dp: Int): Int = overlayManager.dpToPx(dp)
    fun dpToPx(dp: Float): Int = overlayManager.dpToPx(dp)

    fun showControlPanel() {
        logAppEvent(this, "OVERLAY", "Показ главной панели управления")
        controlPanelOverlay.show()
    }

    fun hideControlPanel(openMainApp: Boolean = false) {
        hideTutorial()
        controlPanelOverlay.hide()
        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) { logError(this, e) }
        }
    }

    fun showFloatingStopButton() = controlPanelOverlay.showFloatingStopButton()
    fun hideFloatingStopButton() = controlPanelOverlay.hideFloatingStopButton()

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))
        if (actionsList.isEmpty()) {
            logAppEvent(this, "SCRIPT", "⚠️ Попытка запуска пустого сценария '$name'")
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        logAppEvent(this, "SCRIPT", "▶️ Запуск сценария '$name' (${actionsList.size} шагов)")
        scenarioRunner.start()
    }

    fun stopExecutionLoop() {
        logAppEvent(this, "SCRIPT", "⏹ Остановка выполнения сценария")
        scenarioRunner.stop()
    }

    fun startOverlayRecording() {
        isRecording = true
        logAppEvent(this, "RECORDING", "🔴 Запуск живой записи жестов по экрану")
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        controlPanelOverlay.hide()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        logAppEvent(this, "RECORDING", "⏹ Запись жестов завершена. Всего записано шагов: ${actionsList.size}")
        controlPanelOverlay.show()
        hideFloatingStopButton()
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    fun toggleNumbersVisibility() {
        isNumbersHidden = !isNumbersHidden
        logAppEvent(this, "UI", "Переключение видимости бейджей: isHidden=$isNumbersHidden")
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
        Toast.makeText(this, if (isNumbersHidden) "👁 Номера скрыты" else "👁 Номера показаны", Toast.LENGTH_SHORT).show()
    }

    fun clearAllActions() {
        logAppEvent(this, "SCRIPT", "🗑 Очистка всех шагов сценария (${actionsList.size} шагов было)")
        actionsList.forEach { act ->
            act.startView?.let { overlayManager.safeRemoveView(it) }
            act.endView?.let { overlayManager.safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(x: Float, y: Float, delay: Long, type: ActionType, id: Int) {
        val actionId = if (id == -1) (actionsList.size + 1) else id
        logAppEvent(this, "STEP_ADD", "Добавлен шаг #$actionId [$type] в ($x, $y) с задержкой ${delay}мс")

        val cfg = ActionConfig(
            id = actionId,
            type = type,
            xNorm = normalizeX(x),
            yNorm = normalizeY(y),
            delay = delay
        )
        actionsList.add(cfg)
    }

    fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = overlayManager.dpToPx(36)
        val params = overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        config.endView = endView
        overlayManager.safeAddView(endView, params)
    }

    fun normalizeX(px: Float): Float {
        val (w, _) = overlayManager.getRealScreenSize()
        return (px / w.toFloat()).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val (_, h) = overlayManager.getRealScreenSize()
        return (px / h.toFloat()).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val (w, h) = overlayManager.getRealScreenSize()
        return Pair((nx * w).coerceIn(0f, w.toFloat()), (ny * h).coerceIn(0f, h.toFloat()))
    }

    fun randomOffset(radius: Int): PointF = gestureExecutor.randomOffset(radius)

    fun performClickWithCallback(x: Float, y: Float, duration: Long = globalClickDurationMs, onComplete: ((Boolean) -> Unit)? = null) {
        gestureExecutor.performClickWithCallback(x, y, duration, onComplete)
    }

    fun showClickVisualizer(x: Float, y: Float) = clickVisualizerOverlay.showClickAt(x, y)

    fun captureScreenBitmap(): Bitmap? = captureFrameOverlay.capture()

    fun showScriptsDialog() = ScriptsDialog(this).show()
    fun showEditDialog(config: ActionConfig) = EditActionDialog(this).show(config)

    fun showScriptPickerDialog(title: String, onSelected: (String) -> Unit) {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_select_script_for_export, null)
        val tvTitle = dialogView.findViewById<TextView>(R.id.tvPickerTitle)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutPickerList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnClosePicker)

        tvTitle?.text = title
        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val dir = File(filesDir, "scripts")
        if (dir.exists()) {
            dir.listFiles()?.forEach { file ->
                if (file.name.endsWith(".json")) {
                    val btn = Button(this).apply {
                        text = file.nameWithoutExtension
                        setTextColor(android.graphics.Color.WHITE)
                        setBackgroundColor(android.graphics.Color.parseColor("#1C2541"))
                        setOnClickListener {
                            onSelected(file.nameWithoutExtension)
                            overlayManager.safeRemoveView(dialogView)
                        }
                    }
                    layoutList?.addView(btn)
                }
            }
        }

        btnClose?.setOnClickListener { overlayManager.safeRemoveView(dialogView) }
        overlayManager.safeAddView(dialogView, params)
    }

    fun showAddActionMenu() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val btnClick = dialogView.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = dialogView.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = dialogView.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelAdd)

        val screenSize = overlayManager.getRealScreenSize()
        val spawnX = screenSize.first / 2f
        val spawnY = screenSize.second / 2f

        btnClick?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1); overlayManager.safeRemoveView(dialogView) }
        btnSwipe?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1); spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f); overlayManager.safeRemoveView(dialogView) }
        btnAi?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0); overlayManager.safeRemoveView(dialogView) }
        btnCancel?.setOnClickListener { vibrateFeedback(20L); overlayManager.safeRemoveView(dialogView) }

        overlayManager.safeAddView(dialogView, params)
    }

    fun showTutorialCard() {
        isTutorialActive = true
        if (tutorialCardView != null) {
            tutorialCardView?.visibility = View.VISIBLE
            updateTutorialContent()
            return
        }

        val view = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        tutorialCardView = view

        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
        }

        val btnPrev = view.findViewById<Button>(R.id.btnTutPrev)
        val btnNext = view.findViewById<Button>(R.id.btnTutNext)
        val btnSkip = view.findViewById<Button>(R.id.btnTutSkip)

        btnPrev?.setOnClickListener {
            vibrateFeedback(20L)
            if (currentTutorialStep > 0) {
                currentTutorialStep--
                updateTutorialContent()
            }
        }

        btnNext?.setOnClickListener {
            vibrateFeedback(20L)
            if (currentTutorialStep < 10) {
                currentTutorialStep++
                updateTutorialContent()
            } else {
                hideTutorial()
            }
        }

        btnSkip?.setOnClickListener {
            vibrateFeedback(20L)
            hideTutorial()
        }

        overlayManager.safeAddView(view, params)
        updateTutorialContent()
    }

    private fun updateTutorialContent() {
        if (tutorialCardView == null) return

        if (currentTutorialStep >= 5) {
            controlPanelOverlay.ensureSubMenuVisible()
        }

        val targetButton: View? = controlPanelOverlay.getButtonForStep(currentTutorialStep)
        highlightButton(targetButton)

        uiHandler.post {
            positionTutorialCardAnchored(targetButton)
        }

        val tvTitle = tutorialCardView?.findViewById<TextView>(R.id.tvTutTitle)
        val tvDesc = tutorialCardView?.findViewById<TextView>(R.id.tvTutDesc)
        val btnNext = tutorialCardView?.findViewById<Button>(R.id.btnTutNext)

        when (currentTutorialStep) {
            0 -> {
                tvTitle?.text = "1/11: Запуск [▶]"
                tvDesc?.text = "Запускает и останавливает выполнение всех созданных шагов."
                btnNext?.text = "Далее ►"
            }
            1 -> {
                tvTitle?.text = "2/11: Добавить [+]"
                tvDesc?.text = "Добавляет новый обычный клик, свайп или ИИ-триггер."
                btnNext?.text = "Далее ►"
            }
            2 -> {
                tvTitle?.text = "3/11: ИИ-Сканер [📸]"
                tvDesc?.text = "Открывает прицел для вырезания картинки с экрана и создания ИИ-маски."
                btnNext?.text = "Далее ►"
            }
            3 -> {
                tvTitle?.text = "4/11: Справка [❓]"
                tvDesc?.text = "Повторный вызов этого интерактивного обучения по кнопкам."
                btnNext?.text = "Далее ►"
            }
            4 -> {
                tvTitle?.text = "5/11: Меню [☰]"
                tvDesc?.text = "Разворачивает и сворачивает дополнительную панель инструментов."
                btnNext?.text = "Далее ►"
            }
            5 -> {
                tvTitle?.text = "6/11: Очистить [🗑]"
                tvDesc?.text = "Удаляет абсолютно все мишени и шаги с экрана."
                btnNext?.text = "Далее ►"
            }
            6 -> {
                tvTitle?.text = "7/11: Запись [🔴]"
                tvDesc?.text = "Включает живую запись ваших кликов и свайпов прямо по экрану!"
                btnNext?.text = "Далее ►"
            }
            7 -> {
                tvTitle?.text = "8/11: Джойстик [🕹]"
                tvDesc?.text = "Включает плавающий джойстик для записи жестов свайпа."
                btnNext?.text = "Далее ►"
            }
            8 -> {
                tvTitle?.text = "9/11: Скрипты [📁]"
                tvDesc?.text = "Сохранение текущей схемы шагов в файл и загрузка сохраненных."
                btnNext?.text = "Далее ►"
            }
            9 -> {
                tvTitle?.text = "10/11: Глаз [👁]"
                tvDesc?.text = "Скрывает или показывает бейджи с номерами поверх шагов."
                btnNext?.text = "Далее ►"
            }
            10 -> {
                tvTitle?.text = "11/11: Закрыть [❌]"
                tvDesc?.text = "Выход из панели кликера и возвращение в главное меню."
                btnNext?.text = "Завершить ✔"
            }
        }
    }

    private fun positionTutorialCardAnchored(targetButton: View?) {
        val card = tutorialCardView ?: return
        val panel = controlPanelOverlay.rootView ?: return

        val (screenW, screenH) = overlayManager.getRealScreenSize()
        val loc = IntArray(2)
        if (targetButton != null && targetButton.width > 0) {
            targetButton.getLocationOnScreen(loc)
        } else {
            panel.getLocationOnScreen(loc)
        }

        val anchorX = loc[0]
        val anchorY = loc[1]

        val cardW = dpToPx(240)
        val cardH = dpToPx(150)

        var cardX = anchorX + dpToPx(50)
        var cardY = anchorY + dpToPx(50)

        if (cardX + cardW > screenW - dpToPx(16)) {
            cardX = anchorX - cardW - dpToPx(10)
        }
        if (cardY + cardH > screenH - dpToPx(16)) {
            cardY = anchorY - cardH - dpToPx(10)
        }

        cardX = cardX.coerceIn(dpToPx(10), (screenW - cardW - dpToPx(10)).coerceAtLeast(dpToPx(10)))
        cardY = cardY.coerceIn(dpToPx(40), (screenH - cardH - dpToPx(10)).coerceAtLeast(dpToPx(40)))

        val params = card.layoutParams as? WindowManager.LayoutParams ?: return
        params.gravity = Gravity.TOP or Gravity.START
        params.x = cardX
        params.y = cardY
        overlayManager.safeUpdateViewLayout(card, params)
    }

    private fun highlightButton(button: View?) {
        clearButtonHighlights()
        if (button == null) return

        highlightedButtonAnim = ObjectAnimator.ofPropertyValuesHolder(
            button,
            PropertyValuesHolder.ofFloat(View.SCALE_X, 1.0f, 1.25f, 1.0f),
            PropertyValuesHolder.ofFloat(View.SCALE_Y, 1.0f, 1.25f, 1.0f)
        ).apply {
            duration = 600
            repeatCount = ObjectAnimator.INFINITE
            start()
        }
    }

    private fun clearButtonHighlights() {
        highlightedButtonAnim?.cancel()
        highlightedButtonAnim = null
        controlPanelOverlay.resetAllButtonScales()
    }

    fun hideTutorial() {
        clearButtonHighlights()
        isTutorialActive = false
        tutorialCardView?.let {
            overlayManager.safeRemoveView(it)
            tutorialCardView = null
        }
    }

    fun loadScriptByName(name: String): List<ActionConfig> = scriptRepository.loadScriptByName(name)
    fun saveScriptByName(name: String, actions: List<ActionConfig>) = scriptRepository.saveScriptByName(name, actions)

    fun loadAllTemplatesFromDisk() = templateRepository.loadAllTemplatesFromDisk()
    fun moveTemplateToTrash(index: Int) = templateRepository.moveTemplateToTrash(index)
    fun exportScriptWithTemplates(context: Context, scriptName: String) = scriptRepository.exportScriptWithTemplates(scriptName)

    override fun onDestroy() {
        logAppEvent(this, "SERVICE", "🛑 Служба AutoTap остановлена")
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        super.onDestroy()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    print("✨ Тотальный 360-градусный аудит и патч v37.1.0-PRO успешно применены!")

if __name__ == "__main__":
    run_total_360_audit_patch()