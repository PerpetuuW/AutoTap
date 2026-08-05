import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Интегрирован модуль v35: {rel_path}")

def deploy_v35_final_elements():
    print("🚀 Интеграция 9 недостающих компонентов AutoTap v35 Enterprise (v35.7.0-PRO)...")

    # 1. Gradle Config
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
        versionCode = 2400
        versionName = "35.7.0-PRO"

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

    # 2. TemplateMetadata.kt
    metadata_code = r"""package com.example.autotap.data

import android.graphics.Rect
import org.json.JSONObject

data class TemplateMetadata(
    var width: Int = 0,
    var height: Int = 0,
    var dpi: Int = 480,
    var scale: Float = 1.0f,
    var boundingBox: Rect = Rect(0, 0, 0, 0),
    var similarityPercent: Int = 70,
    var isCircleShape: Boolean = true,
    var version: Int = 1,
    var timestamp: Long = System.currentTimeMillis()
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("width", width)
        put("height", height)
        put("dpi", dpi)
        put("scale", scale.toDouble())
        put("originX", boundingBox.left)
        put("originY", boundingBox.top)
        put("originW", boundingBox.width())
        put("originH", boundingBox.height())
        put("similarityPercent", similarityPercent)
        put("isCircleShape", isCircleShape)
        put("version", version)
        put("timestamp", timestamp)
    }

    companion object {
        fun fromJson(obj: JSONObject): TemplateMetadata {
            val x = obj.optInt("originX", 0)
            val y = obj.optInt("originY", 0)
            val w = obj.optInt("originW", 0)
            val h = obj.optInt("originH", 0)
            return TemplateMetadata(
                width = obj.optInt("width", w),
                height = obj.optInt("height", h),
                dpi = obj.optInt("dpi", 480),
                scale = obj.optDouble("scale", 1.0).toFloat(),
                boundingBox = Rect(x, y, x + w, y + h),
                similarityPercent = obj.optInt("similarityPercent", 70),
                isCircleShape = obj.optBoolean("isCircleShape", true),
                version = obj.optInt("version", 1),
                timestamp = obj.optLong("timestamp", System.currentTimeMillis())
            )
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/data/TemplateMetadata.kt", metadata_code)

    # 3. MaskCalibrator.kt
    calibrator_code = r"""package com.example.autotap.engine

import android.graphics.*

object MaskCalibrator {
    fun normalizeDpi(bmp: Bitmap, sourceDpi: Int, targetDpi: Int): Bitmap {
        if (sourceDpi == targetDpi || sourceDpi <= 0 || targetDpi <= 0) return bmp
        val factor = targetDpi.toFloat() / sourceDpi.toFloat()
        val nw = (bmp.width * factor).toInt().coerceAtLeast(1)
        val nh = (bmp.height * factor).toInt().coerceAtLeast(1)
        return Bitmap.createScaledBitmap(bmp, nw, nh, true)
    }

    fun adjustBrightnessContrast(bmp: Bitmap, brightness: Float = 0f, contrast: Float = 1f): Bitmap {
        val cm = ColorMatrix(floatArrayOf(
            contrast, 0f, 0f, 0f, brightness,
            0f, contrast, 0f, 0f, brightness,
            0f, 0f, contrast, 0f, brightness,
            0f, 0f, 0f, 1f, 0f
        ))
        val out = Bitmap.createBitmap(bmp.width, bmp.height, bmp.config ?: Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { colorFilter = ColorMatrixColorFilter(cm) }
        canvas.drawBitmap(bmp, 0f, 0f, paint)
        return out
    }

    fun adaptMask(bmp: Bitmap): Bitmap {
        return adjustBrightnessContrast(bmp, 10f, 1.1f)
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/MaskCalibrator.kt", calibrator_code)

    # 4. MultiFrameMatcher.kt & HybridCascadeMatcher.kt
    multi_frame_code = r"""package com.example.autotap.engine

import android.graphics.Bitmap
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.TemplateMatcher
import org.json.JSONObject

object MultiFrameMatcher {
    fun matchMultiFrame(
        frames: List<Bitmap>,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): MatchCandidate? {
        if (frames.isEmpty()) return null
        val candidates = ArrayList<MatchCandidate>()
        for (frame in frames) {
            val match = TemplateMatcher.findTemplateCandidatesCoarseFine(frame, template, meta, config).firstOrNull()
            if (match != null) candidates.add(match)
        }
        if (candidates.isEmpty()) return null
        return candidates.maxByOrNull { it.score }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/MultiFrameMatcher.kt", multi_frame_code)

    hybrid_code = r"""package com.example.autotap.engine

import android.graphics.Bitmap
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.TemplateMatcher
import org.json.JSONObject

object HybridCascadeMatcher {
    fun cascadeSearch(
        screen: Bitmap,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): List<MatchCandidate> {
        val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(screen, template, meta, config)
        return candidates.take(3)
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/HybridCascadeMatcher.kt", hybrid_code)

    # 5. ScenarioRunner.kt
    runner_code = r"""package com.example.autotap.engine

import com.example.autotap.ActionConfig
import com.example.autotap.MyAutoClickService

class ScenarioRunner(private val service: MyAutoClickService) {
    @Volatile var isRunning: Boolean = false
        private set

    var currentStepIndex: Int = 0
        private set

    fun start() {
        isRunning = true
        currentStepIndex = 0
        service.scriptExecutor.startExecutionLoop()
    }

    fun pause() {
        isRunning = false
        service.scriptExecutor.stopExecutionLoop()
    }

    fun stop() {
        isRunning = false
        currentStepIndex = 0
        service.scriptExecutor.stopExecutionLoop()
    }

    fun nextStep(totalSteps: Int) {
        if (totalSteps > 0) {
            currentStepIndex = (currentStepIndex + 1) % totalSteps
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/ScenarioRunner.kt", runner_code)

    # 6. OverlayBase.kt
    overlay_base_code = r"""package com.example.autotap.ui.base

import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService

abstract class OverlayBase(
    protected val service: MyAutoClickService,
    protected val layoutResId: Int
) {
    var rootView: View? = null
        protected set

    val isShowing: Boolean
        get() = rootView != null && rootView?.parent != null

    open fun show() {
        if (isShowing) return
        val view = LayoutInflater.from(service).inflate(layoutResId, null)
        rootView = view
        val params = createParams()
        onViewInflated(view)
        service.overlayManager.safeAddView(view, params)
    }

    open fun hide() {
        rootView?.let { service.overlayManager.safeRemoveView(it) }
        rootView = null
    }

    protected open fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams()
    }

    protected abstract fun onViewInflated(view: View)

    protected fun <T : View> findViewById(id: Int): T? {
        return rootView?.findViewById(id)
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt", overlay_base_code)

    # 7. ClickVisualizerOverlay.kt с анимациями Fade/Ripple
    click_vis_code = r"""package com.example.autotap.ui.overlays

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ClickVisualizerOverlay(private val service: MyAutoClickService) {

    fun showClickAt(x: Float, y: Float) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_beacon_ring, null)
        val sizePx = service.dpToPx(40)
        val params = service.overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            this.x = (x - sizePx / 2f).toInt()
            this.y = (y - sizePx / 2f).toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.alpha = 0f
        view.scaleX = 0.4f
        view.scaleY = 0.4f

        val fadeIn = ObjectAnimator.ofFloat(view, View.ALPHA, 0f, 1f).setDuration(80)
        val scaleX = ObjectAnimator.ofFloat(view, View.SCALE_X, 0.4f, 1.8f).setDuration(280)
        val scaleY = ObjectAnimator.ofFloat(view, View.SCALE_Y, 0.4f, 1.8f).setDuration(280)
        val fadeOut = ObjectAnimator.ofFloat(view, View.ALPHA, 1f, 0f).setDuration(150)
        fadeOut.startDelay = 150

        AnimatorSet().apply {
            playTogether(fadeIn, scaleX, scaleY, fadeOut)
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: android.animation.Animator) {
                    service.overlayManager.safeRemoveView(view)
                }
            })
            start()
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/ClickVisualizerOverlay.kt", click_vis_code)

    # 8. TemplateRepository.kt с init(context) и Singleton
    template_repo_code = r"""package com.example.autotap.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.widget.Toast
import com.example.autotap.MyAutoClickService
import com.example.autotap.TemplateMatcher
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream

class TemplateRepository private constructor(private val context: Context) {

    companion object {
        @Volatile private var INSTANCE: TemplateRepository? = null

        fun init(context: Context): TemplateRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: TemplateRepository(context.applicationContext).also { INSTANCE = it }
            }
        }

        val instance: TemplateRepository
            get() = INSTANCE ?: throw IllegalStateException("TemplateRepository not initialized. Call init(context) first.")
    }

    val globalTemplates = ArrayList<Bitmap>()
    val globalTemplatesNames = ArrayList<String>()

    fun getTemplateMetadataFile(maskPath: String): File {
        val maskFile = File(maskPath)
        val parent = maskFile.parentFile ?: context.filesDir
        return File(parent, "${maskFile.nameWithoutExtension}.json")
    }

    fun loadTemplateMetadata(maskPath: String): JSONObject? {
        try {
            if (maskPath.isEmpty()) return null
            val metaFile = getTemplateMetadataFile(maskPath)
            if (metaFile.exists()) return JSONObject(metaFile.readText())
        } catch (_: Exception) {}
        return null
    }

    fun loadFullBitmap(maskPath: String): Bitmap? {
        val maskFile = File(maskPath)
        val parent = maskFile.parentFile ?: return null
        val timestamp = maskFile.name.removePrefix("mask_").removeSuffix(".png")
        val fullFile = File(parent, "full_${timestamp}.png")
        if (!fullFile.exists()) return null
        return BitmapFactory.decodeFile(fullFile.absolutePath)
    }

    fun recordSuccessfulMatch(maskPath: String, matchPatch: Bitmap) {
        try {
            val maskFile = File(maskPath)
            if (!maskFile.exists()) return

            val name = maskFile.nameWithoutExtension
            val patchDir = File(File(context.filesDir, "templates/patches"), name).apply { mkdirs() }
            val patchFile = File(patchDir, "patch_${System.currentTimeMillis()}.png")

            FileOutputStream(patchFile).use { out -> matchPatch.compress(Bitmap.CompressFormat.PNG, 100, out) }

            val patchFiles = patchDir.listFiles()?.filter { file -> file.name.endsWith(".png") } ?: emptyList()
            if (patchFiles.size >= 5) {
                val patchBitmaps = patchFiles.mapNotNull<File, Bitmap> { file -> BitmapFactory.decodeFile(file.absolutePath) }
                if (patchBitmaps.isNotEmpty()) {
                    val meta = loadTemplateMetadata(maskPath)
                    val isCircle = meta?.optBoolean("isCircleShape", true) ?: true
                    val consensusMask = TemplateMatcher.aggregateMultiFrameMask(patchBitmaps, isCircle)

                    FileOutputStream(maskFile).use { out -> consensusMask.compress(Bitmap.CompressFormat.PNG, 100, out) }

                    if (meta != null) {
                        meta.put("version", meta.optInt("version", 1) + 1)
                        FileOutputStream(getTemplateMetadataFile(maskPath)).use { out ->
                            out.write(meta.toString().toByteArray(Charsets.UTF_8))
                        }
                    }

                    patchFiles.forEach { it.delete() }
                    patchDir.delete()
                }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun loadAllTemplatesFromDisk() {
        try {
            globalTemplates.forEach { try { it.recycle() } catch (_: Exception) {} }
            globalTemplates.clear()
            globalTemplatesNames.clear()

            val baseDir = File(context.filesDir, "templates")
            if (baseDir.exists()) {
                baseDir.walkTopDown()
                    .filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }
                    .sortedBy { it.lastModified() }
                    .forEach { file ->
                        BitmapFactory.decodeFile(file.absolutePath)?.let { bmp ->
                            globalTemplates.add(bmp)
                            globalTemplatesNames.add(file.absolutePath)
                        }
                    }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun moveTemplateToTrash(index: Int) {
        if (index !in globalTemplatesNames.indices) return
        try {
            val maskPath = globalTemplatesNames[index]
            val maskFile = File(maskPath)
            if (maskFile.exists()) maskFile.delete()
            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)
            Toast.makeText(context, "🗑 Шаблон удален", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/data/TemplateRepository.kt", template_repo_code)

    # 9. ScriptRepository.kt с init(context) и Singleton
    script_repo_code = r"""package com.example.autotap.data

import android.content.Context
import androidx.core.content.FileProvider
import com.example.autotap.ActionConfig
import com.example.autotap.MyAutoClickService
import org.json.JSONArray
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class ScriptRepository private constructor(private val context: Context) {

    companion object {
        @Volatile private var INSTANCE: ScriptRepository? = null

        fun init(context: Context): ScriptRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: ScriptRepository(context.applicationContext).also { INSTANCE = it }
            }
        }

        val instance: ScriptRepository
            get() = INSTANCE ?: throw IllegalStateException("ScriptRepository not initialized. Call init(context) first.")
    }

    private fun getScriptsDir(): File {
        val dir = File(context.filesDir, "scripts")
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun loadScriptByName(name: String): List<ActionConfig> {
        val list = ArrayList<ActionConfig>()
        try {
            val file = File(getScriptsDir(), "$name.json")
            val bakFile = File(getScriptsDir(), "$name.json.bak")
            val targetFile = if (file.exists() && file.length() > 0) file else bakFile

            if (targetFile != null && targetFile.exists()) {
                val jsonArray = JSONArray(targetFile.readText())
                for (i in 0 until jsonArray.length()) {
                    list.add(ActionConfig.fromJson(jsonArray.getJSONObject(i)))
                }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
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
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun exportScriptWithTemplates(scriptName: String) {
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
            val shareIntent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(android.content.Intent.EXTRA_STREAM, uri)
                addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(android.content.Intent.createChooser(shareIntent, "Экспорт сценария v35"))
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/data/ScriptRepository.kt", script_repo_code)

    # 10. Обновление MyAutoClickService.kt для инициализации синглтонов
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScenarioRunner
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.*
import java.io.File

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

    // --- STATE ---
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        // Initialize singletons & core subsystems
        templateRepository = TemplateRepository.init(this)
        scriptRepository = ScriptRepository.init(this)

        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        scenarioRunner = ScenarioRunner(this)
        aiScannerEngine = AiScannerEngine(this)

        // Initialize overlays
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

        Toast.makeText(this, "AutoTap v35.7.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    fun vibrateFeedback(ms: Long = 25L) = gestureExecutor.vibrateFeedback(ms)

    fun showControlPanel() = controlPanelOverlay.show()

    fun hideControlPanel(openMainApp: Boolean = false) {
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
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        scenarioRunner.start()
    }

    fun stopExecutionLoop() {
        scenarioRunner.stop()
    }

    fun startOverlayRecording() {
        isRecording = true
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        controlPanelOverlay.hide()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        controlPanelOverlay.show()
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
            act.startView?.let { overlayManager.safeRemoveView(it) }
            act.endView?.let { overlayManager.safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(x: Float, y: Float, delay: Long, type: ActionType, id: Int) {
        val cfg = ActionConfig(
            id = if (id == -1) (actionsList.size + 1) else id,
            type = type,
            xNorm = normalizeX(x),
            yNorm = normalizeY(y),
            delay = delay
        )
        actionsList.add(cfg)
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

    fun showClickVisualizer(x: Float, y: Float) = clickVisualizerOverlay.showClickAt(x, y)

    fun captureScreenBitmap(): Bitmap? = captureFrameOverlay.capture()

    fun showScriptsDialog() = ScriptsDialog(this).show()
    fun showEditDialog(config: ActionConfig) = EditActionDialog(this).show(config)

    fun loadScriptByName(name: String): List<ActionConfig> = scriptRepository.loadScriptByName(name)
    fun saveScriptByName(name: String, actions: List<ActionConfig>) = scriptRepository.saveScriptByName(name, actions)

    fun loadAllTemplatesFromDisk() = templateRepository.loadAllTemplatesFromDisk()
    fun moveTemplateToTrash(index: Int) = templateRepository.moveTemplateToTrash(index)
    fun exportScriptWithTemplates(context: Context, scriptName: String) = scriptRepository.exportScriptWithTemplates(scriptName)

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        super.onDestroy()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    print("✨ Все 9 компонентов успешно интегрированы в AutoTap v35.7.0-PRO!")

if __name__ == "__main__":
    deploy_v35_final_elements()