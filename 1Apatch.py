import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Развернут модуль v35: {rel_path}")

def fix_random_offset_error():
    print("🚀 Исправление ошибки randomOffset v35.6.0-PRO...")

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
        versionCode = 2390
        versionName = "35.6.0-PRO"

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

    # 2. core/GestureExecutor.kt
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
}
"""
    write_file("app/src/main/java/com/example/autotap/core/GestureExecutor.kt", gesture_code)

    # 3. MyAutoClickService.kt
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PointF
import android.view.accessibility.AccessibilityEvent
import android.widget.Toast
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
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
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // --- UI OVERLAYS ---
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay

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

        // Initialize core subsystems
        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        aiScannerEngine = AiScannerEngine(this)
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)

        // Initialize overlays
        controlPanelOverlay = ControlPanelOverlay(this)
        joystickOverlay = JoystickOverlay(this)
        captureFrameOverlay = CaptureFrameOverlay(this)
        debuggerOverlay = ScenarioDebuggerOverlay(this)

        templateRepository.loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v35.6.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    // --- PUBLIC API FOR SUBSYSTEMS & OVERLAYS ---

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
        isPlaying = true
        scriptExecutor.startExecutionLoop()
    }

    fun stopExecutionLoop() {
        isPlaying = false
        scriptExecutor.stopExecutionLoop()
    }

    fun startOverlayRecording() {
        isRecording = true
        actionsList.forEach { act ->
            act.startView?.visibility = android.view.View.INVISIBLE
            act.endView?.visibility = android.view.View.INVISIBLE
        }
        controlPanelOverlay.hide()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        controlPanelOverlay.show()
        hideFloatingStopButton()
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) android.view.View.INVISIBLE else android.view.View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) android.view.View.INVISIBLE else android.view.View.VISIBLE
        }
    }

    fun toggleNumbersVisibility() {
        isNumbersHidden = !isNumbersHidden
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) android.view.View.INVISIBLE else android.view.View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) android.view.View.INVISIBLE else android.view.View.VISIBLE
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

    fun randomOffset(radius: Int): PointF {
        if (radius <= 0) return PointF(0f, 0f)
        val dx = (-radius..radius).random().toFloat()
        val dy = (-radius..radius).random().toFloat()
        return PointF(dx, dy)
    }

    fun showClickVisualizer(x: Float, y: Float) = controlPanelOverlay.showClickVisualizer(x, y)

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

    print("✨ Ошибка randomOffset успешно устранена!")

if __name__ == "__main__":
    fix_random_offset_error()