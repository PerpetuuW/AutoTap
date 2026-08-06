import os
import sys
import re

def validate_kotlin(content, filename):
    # Очистка комментариев и строковых литералов перед проверкой скобок
    clean = re.sub(r'/\*[\s\S]*?\*/', '', content)
    clean = re.sub(r'//.*', '', clean)
    clean = re.sub(r'"""[\s\S]*?"multiline"""', '""', clean)
    clean = re.sub(r'"([^"\\]|\\.)*"', '""', clean)
    clean = re.sub(r"'([^'\\]|\\.)*'", "''", clean)

    brackets = {'(': ')', '{': '}', '[': ']'}
    stack = []
    for char in clean:
        if char in brackets.keys():
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Лишняя закрывающая скобка '{char}'")
            top = stack.pop()
            if brackets[top] != char:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Несоответствие скобок '{top}' и '{char}'")
    if stack:
        raise ValueError(f"Ошибка синтаксиса в {filename}: Незакрытые скобки {stack}")

    forbidden = ["TODO()", "// остальной код", "// TODO"]
    for item in forbidden:
        if item in content:
            raise ValueError(f"Обнаружена запрещенная заглушка '{item}' в файле {filename}")

files = {}

# 1. build.gradle.kts (Top-level)
files["build.gradle.kts"] = """// Top-level build file
plugins {
    id("com.android.application") version "9.3.1" apply false
    id("org.jetbrains.kotlin.android") version "2.2.10" apply false
}
"""

# 2. settings.gradle.kts
files["settings.gradle.kts"] = """pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\\\.android.*")
                includeGroupByRegex("com\\\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}
plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "AutoTap"
include(":app")
"""

# 3. gradle.properties
files["gradle.properties"] = """android.useAndroidX=true
android.enableJetifier=false
android.builtInKotlin=false
android.newDsl=false
android.sync.suppressAgpWarnings=UNSUPPORTED_PROJECT_OPTION_USE,DEPRECATED_DSL,LIBRARY_CONSTRAINTS_SHOULD_BE_DISABLED
android.generateSyncIssueWhenLibraryConstraintsAreEnabled=false
"""

# 4. app/build.gradle.kts
files["app/build.gradle.kts"] = """plugins {
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
        versionCode = 4000
        versionName = "40.0.0-PRO"

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

# 5. AndroidManifest.xml
files["app/src/main/AndroidManifest.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AutoTap">

        <activity
            android:name="com.example.autotap.MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name="com.example.autotap.ui.LogViewerActivity"
            android:exported="false"
            android:label="Диагностика и Логи" />

        <service
            android:name="com.example.autotap.MyAutoClickService"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>

    </application>

</manifest>
"""

# 6. StructuredLogger.kt
files["app/src/main/java/com/example/autotap/logger/StructuredLogger.kt"] = """package com.example.autotap.logger

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object StructuredLogger {
    private const val MAX_LOG_SIZE = 524288L // 512 KB
    private var logFile: File? = null

    fun init(context: Context) {
        val dir = context.getExternalFilesDir(null) ?: context.filesDir
        logFile = File(dir, "error_log.txt")
        rotateLogIfNeeded()
    }

    @Synchronized
    fun logDiagnostic(category: String, message: String) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        val formatted = "[$timestamp] [$category] $message\\n"
        println(formatted)
        appendToLogFile(formatted)
    }

    @Synchronized
    fun logError(category: String, message: String, throwable: Throwable? = null) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        val errText = throwable?.stackTraceToString() ?: ""
        val formatted = "[$timestamp] [ERROR] [$category] $message $errText\\n"
        System.err.println(formatted)
        appendToLogFile(formatted)
    }

    private fun appendToLogFile(text: String) {
        val file = logFile ?: return
        try {
            rotateLogIfNeeded()
            file.appendText(text)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun rotateLogIfNeeded() {
        val file = logFile ?: return
        if (file.exists() && file.length() > MAX_LOG_SIZE) {
            val content = file.readText()
            val halfIndex = content.length / 2
            val trimmedContent = "...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\\n" + content.substring(halfIndex)
            file.writeText(trimmedContent)
        }
    }

    fun getLogFile(): File? = logFile
}

fun logError(category: String, message: String, throwable: Throwable? = null) {
    StructuredLogger.logError(category, message, throwable)
}

fun logDiagnostic(category: String, message: String) {
    StructuredLogger.logDiagnostic(category, message)
}
"""

# 7. ActionConfig.kt
files["app/src/main/java/com/example/autotap/model/ActionConfig.kt"] = """package com.example.autotap.model

import android.graphics.PointF

enum class ActionType {
    CLICK, SWIPE, LONG_PRESS, AI_SEARCH, WAIT, LOAD_SCRIPT, JOYSTICK_PATH
}

data class ActionConfig(
    var type: ActionType = ActionType.CLICK,
    var xNorm: Float = 0.5f,
    var yNorm: Float = 0.5f,
    var endXNorm: Float = 0.5f,
    var endYNorm: Float = 0.5f,
    var randomRadius: Float = 0f,
    var delay: Long = 500L,
    var holdDuration: Long = 100L,
    var selectedTemplateIndex: Int = 0,
    var multiTemplateIndices: List<Int> = emptyList(),
    var similarityPercent: Int = 85,
    var scanIntervalSeconds: Float = 0.1f,
    var clickAiTarget: Boolean = false,
    var loopUntilStopped: Boolean = true,
    var jumpToStepOnMatch: Int? = null,
    var jumpToStepOnFail: Int? = null,
    var targetScriptToLoad: String? = null,
    var customSearchArea: Boolean = false,
    var searchAreaX: Int = 0,
    var searchAreaY: Int = 0,
    var searchAreaW: Int = 0,
    var searchAreaH: Int = 0,
    var shapeOnlyMode: Boolean = false,
    var autoTuningMode: Boolean = false,
    var hybridCascadeMode: Boolean = true,
    var multiScaleSearch: Boolean = true,
    var joystickPath: List<PointF> = emptyList(),
    var swipePath: List<PointF> = emptyList(),
    var longPressDuration: Long = 500L,
    var clickOffsetX: Int = 0,
    var clickOffsetY: Int = 0
)
"""

# 8. ExtensionsAndUtils.kt
files["app/src/main/java/com/example/autotap/ExtensionsAndUtils.kt"] = """package com.example.autotap

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.graphics.PointF
import android.graphics.Rect
import android.graphics.RectF
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import com.example.autotap.logger.StructuredLogger

object CoordConverter {
    fun toNormalizedPoint(pt: PointF, widthPx: Int, heightPx: Int): PointF {
        val w = widthPx.coerceAtLeast(1).toFloat()
        val h = heightPx.coerceAtLeast(1).toFloat()
        return PointF((pt.x / w).coerceIn(0f, 1f), (pt.y / h).coerceIn(0f, 1f))
    }

    fun toPxPoint(ptNorm: PointF, widthPx: Int, heightPx: Int): PointF {
        return PointF(ptNorm.x * widthPx, ptNorm.y * heightPx)
    }

    fun toNormalizedRect(rect: Rect, widthPx: Int, heightPx: Int): RectF {
        val w = widthPx.coerceAtLeast(1).toFloat()
        val h = heightPx.coerceAtLeast(1).toFloat()
        return RectF(
            (rect.left / w).coerceIn(0f, 1f),
            (rect.top / h).coerceIn(0f, 1f),
            (rect.right / w).coerceIn(0f, 1f),
            (rect.bottom / h).coerceIn(0f, 1f)
        )
    }

    fun toPxRect(rectNorm: RectF, widthPx: Int, heightPx: Int): Rect {
        return Rect(
            (rectNorm.left * widthPx).toInt(),
            (rectNorm.top * heightPx).toInt(),
            (rectNorm.right * widthPx).toInt(),
            (rectNorm.bottom * heightPx).toInt()
        )
    }
}

fun Int.dpToPx(context: Context): Int {
    return (this * context.resources.displayMetrics.density).toInt()
}

fun Float.dpToPx(context: Context): Int {
    return (this * context.resources.displayMetrics.density).toInt()
}

fun Context.dpToPx(dp: Int): Int {
    return (dp * resources.displayMetrics.density).toInt()
}

fun Context.getRealScreenSize(): Point {
    val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
    return wm.getRealScreenSizeCompat()
}

fun WindowManager.getRealScreenSizeCompat(): Point {
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        val bounds = currentWindowMetrics.bounds
        Point(bounds.width(), bounds.height())
    } else {
        val point = Point()
        @Suppress("DEPRECATION")
        defaultDisplay?.getRealSize(point)
        point
    }
}

fun View.findViewByNames(vararg idNames: String): View? {
    for (name in idNames) {
        val id = context.resources.getIdentifier(name, "id", context.packageName)
        if (id != 0) {
            val found = findViewById<View>(id)
            if (found != null) return found
        }
    }
    return null
}

fun View.bindClickByNames(vararg idNames: String, onClick: (View) -> Unit): Boolean {
    val target = findViewByNames(*idNames)
    if (target != null) {
        target.setOnClickListener(onClick)
        return true
    }
    return false
}

fun createOverlayParams(
    width: Int = WindowManager.LayoutParams.WRAP_CONTENT,
    height: Int = WindowManager.LayoutParams.WRAP_CONTENT,
    gravity: Int = Gravity.TOP or Gravity.START,
    flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
    x: Int = 100,
    y: Int = 200
): WindowManager.LayoutParams {
    val windowType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
    } else {
        @Suppress("DEPRECATION")
        WindowManager.LayoutParams.TYPE_PHONE
    }

    return WindowManager.LayoutParams(
        width, height,
        windowType,
        flags,
        PixelFormat.TRANSLUCENT
    ).apply {
        this.gravity = gravity
        this.x = x
        this.y = y
    }
}

fun WindowManager.safeAddView(view: View, params: WindowManager.LayoutParams): Boolean {
    return try {
        addView(view, params)
        true
    } catch (e: Exception) {
        e.printStackTrace()
        false
    }
}

fun WindowManager.safeRemoveView(view: View): Boolean {
    return try {
        removeView(view)
        true
    } catch (e: Exception) {
        e.printStackTrace()
        false
    }
}

fun Context.vibrateFeedback() {
    try {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            getSystemService(Vibrator::class.java)
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        } ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(30L, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(30L)
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
}

fun logAppEvent(category: String, message: String) {
    StructuredLogger.logDiagnostic(category, message)
}
"""

# 9. MyAutoClickService.kt
files["app/src/main/java/com/example/autotap/MyAutoClickService.kt"] = """package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.PointF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Display
import android.view.accessibility.AccessibilityEvent
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.GestureExecutor
import com.example.autotap.engine.RecordingEngine
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.engine.TutorialEngine
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.ui.base.OverlayManager
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class MyAutoClickService : AccessibilityService() {

    companion object {
        @Volatile var instance: MyAutoClickService? = null
    }

    val actionsList = mutableListOf<ActionConfig>()
    @Volatile var isPlaying = false

    var globalClickDurationMs: Long = 120L
    var globalSwipeDurationMs: Long = 300L
    var globalPreScreenshotDelayMs: Long = 250L

    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var recordingEngine: RecordingEngine
    lateinit var tutorialEngine: TutorialEngine
    lateinit var scriptRepository: ScriptRepository
    lateinit var templateRepository: TemplateRepository
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var overlayManager: OverlayManager

    private val mainHandler = Handler(Looper.getMainLooper())
    private val gestureQueue = ConcurrentLinkedQueue<GestureTask>()
    @Volatile private var isExecutingGesture = false

    data class GestureTask(
        val stroke: GestureDescription.StrokeDescription,
        val description: String,
        val callback: ((Boolean) -> Unit)?
    )

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        StructuredLogger.init(this)

        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        recordingEngine = RecordingEngine(this)
        tutorialEngine = TutorialEngine(this)
        scriptRepository = ScriptRepository(this)
        templateRepository = TemplateRepository(this)
        aiScannerEngine = AiScannerEngine(this)
        overlayManager = OverlayManager(this)

        logDiagnostic("OVERLAY", "MyAutoClickService v40 полностью инициализирован.")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val type = event?.eventType ?: return
        logDiagnostic("GESTURE", "Событие Accessibility: $type")
    }

    override fun onInterrupt() {
        logError("ERROR", "Служба Accessibility прервана системой.", null)
        gestureQueue.clear()
        isExecutingGesture = false
    }

    override fun onDestroy() {
        super.onDestroy()
        if (instance == this) {
            instance = null
        }
    }

    fun isOverlayArea(x: Float, y: Float): Boolean {
        if (!::overlayManager.isInitialized) return false
        val ptX = x.toInt()
        val ptY = y.toInt()

        if (overlayManager.controlPanel.isShowing && overlayManager.controlPanel.getBounds().contains(ptX, ptY)) return true
        if (overlayManager.joystickOverlay.isShowing && overlayManager.joystickOverlay.getBounds().contains(ptX, ptY)) return true
        if (overlayManager.debuggerOverlay.isShowing && overlayManager.debuggerOverlay.getBounds().contains(ptX, ptY)) return true

        return false
    }

    fun dispatchGestureTask(stroke: GestureDescription.StrokeDescription, description: String, callback: ((Boolean) -> Unit)?) {
        gestureQueue.add(GestureTask(stroke, description, callback))
        processNextGesture()
    }

    private fun processNextGesture() {
        if (isExecutingGesture) return
        val task = gestureQueue.poll() ?: return
        isExecutingGesture = true

        val builder = GestureDescription.Builder()
        builder.addStroke(task.stroke)
        val gesture = builder.build()

        val resultCallback = object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                isExecutingGesture = false
                task.callback?.invoke(true)
                mainHandler.post { processNextGesture() }
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                isExecutingGesture = false
                task.callback?.invoke(false)
                mainHandler.post { processNextGesture() }
            }
        }

        val dispatched = dispatchGesture(gesture, resultCallback, mainHandler)
        if (!dispatched) {
            isExecutingGesture = false
            task.callback?.invoke(false)
            mainHandler.post { processNextGesture() }
        }
    }

    fun resolveNormalizedPoint(xNorm: Float, yNorm: Float): PointF {
        val metrics = resources.displayMetrics
        return PointF(xNorm * metrics.widthPixels, yNorm * metrics.heightPixels)
    }

    fun vibrateFeedback() {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                getSystemService(Vibrator::class.java)
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            } ?: return

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(30L, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(30L)
            }
        } catch (e: Exception) {
            logError("ERROR", "Ошибка обратной связи вибрации", e)
        }
    }

    fun addNewActionAtPosition(xNorm: Float, yNorm: Float) {
        actionsList.add(ActionConfig(xNorm = xNorm, yNorm = yNorm))
        if (recordingEngine.isRecording) {
            recordingEngine.recordClick(xNorm, yNorm)
        }
        logDiagnostic("SCRIPT", "Добавлено новое действие на позиции ($xNorm, $yNorm)")
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        scriptRepository.saveScript(name, actions)
    }

    fun loadScriptByName(name: String): Boolean {
        val loaded = scriptRepository.loadScript(name)
        if (loaded.isNotEmpty()) {
            actionsList.clear()
            actionsList.addAll(loaded)
            return true
        }
        return false
    }

    fun captureScreenBitmapAsync(callback: (Bitmap?) -> Unit) {
        val delayMs = globalPreScreenshotDelayMs.coerceAtLeast(0L)
        mainHandler.postDelayed({
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    takeScreenshot(
                        Display.DEFAULT_DISPLAY,
                        mainExecutor,
                        object : TakeScreenshotCallback {
                            override fun onSuccess(screenshotResult: ScreenshotResult) {
                                val buffer = screenshotResult.hardwareBuffer
                                val bitmap = Bitmap.wrapHardwareBuffer(buffer, screenshotResult.colorSpace)
                                    ?.copy(Bitmap.Config.ARGB_8888, true)
                                buffer.close()
                                callback(bitmap)
                            }

                            override fun onFailure(errorCode: Int) {
                                logError("AI_SCANNER", "Ошибка takeScreenshot код: $errorCode", null)
                                callback(generateFallbackFrame())
                            }
                        }
                    )
                } catch (e: Exception) {
                    logError("AI_SCANNER", "Ошибка вызова takeScreenshot API", e)
                    callback(generateFallbackFrame())
                }
            } else {
                callback(generateFallbackFrame())
            }
        }, delayMs)
    }

    fun captureScreenBitmap(): Bitmap? {
        var result: Bitmap? = null
        val latch = CountDownLatch(1)
        captureScreenBitmapAsync { bmp ->
            result = bmp
            latch.countDown()
        }
        try {
            latch.await(1500, TimeUnit.MILLISECONDS)
        } catch (_: Exception) {}
        return result ?: generateFallbackFrame()
    }

    private fun generateFallbackFrame(): Bitmap {
        val metrics = resources.displayMetrics
        val w = metrics.widthPixels.coerceAtLeast(400)
        val h = metrics.heightPixels.coerceAtLeast(600)
        val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bmp)
        canvas.drawColor(Color.DKGRAY)
        return bmp
    }

    fun showControlPanel() {
        overlayManager.showControlPanel()
    }

    fun hideControlPanel() {
        overlayManager.hideControlPanel()
    }

    fun showFloatingStopButton() {
        overlayManager.showFloatingStopButton()
    }

    fun hideFloatingStopButton() {
        overlayManager.hideFloatingStopButton()
    }

    fun showClickVisualizer(x: Float, y: Float) {
        overlayManager.showClickVisualizer(x, y)
    }
}
"""

# 10. MainActivity.kt
files["app/src/main/java/com/example/autotap/MainActivity.kt"] = """package com.example.autotap

import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.LogViewerActivity

class MainActivity : AppCompatActivity() {

    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository
    lateinit var actionEditorEngine: ActionEditorEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        StructuredLogger.init(this)

        initRepositories()
        initEngines()

        try {
            setContentView(R.layout.activity_main)
            logDiagnostic("UI", "Главное меню успешно надуло activity_main.xml")
        } catch (e: Exception) {
            logError("UI", "Ошибка установки setContentView(R.layout.activity_main)", e)
        }

        val root = window.decorView.findViewById<View>(android.R.id.content)

        val versionName = try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: getString(R.string.app_version)
        } catch (_: Exception) {
            getString(R.string.app_version)
        }

        (root.findViewByNames("tvVersion") as? TextView)?.text = versionName
        (root.findViewByNames("tvSubTitle") as? TextView)?.text = "Комплекс Автоматизации и ИИ Поиска"

        root.bindClickByNames("btnStartPanel") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.showControlPanel()
                logDiagnostic("UI", "Запуск панели оверлеев.")
            } else {
                Toast.makeText(this, "Сначала включите Accessibility Service!", Toast.LENGTH_LONG).show()
                logError("UI", "MyAutoClickService не запущен!", null)
            }
        }

        root.bindClickByNames("btnAccessibility") {
            try {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                logDiagnostic("UI", "Переход в настройки Accessibility.")
            } catch (e: Exception) {
                logError("UI", "Ошибка перехода в настройки Accessibility", e)
            }
        }

        root.bindClickByNames("btnOverlay") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this@MainActivity)) {
                try {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivity(intent)
                    logDiagnostic("UI", "Запрос разрешения оверлея.")
                } catch (e: Exception) {
                    logError("UI", "Ошибка запроса разрешения оверлея", e)
                }
            } else {
                Toast.makeText(this, "Разрешение оверлея уже предоставлено!", Toast.LENGTH_SHORT).show()
            }
        }

        root.bindClickByNames("btnAppDetails", "btnPermissionsHelp") {
            openRestrictedSettingsMenu()
        }

        root.bindClickByNames("btnShowLogs") {
            try {
                startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
            } catch (e: Exception) {
                logError("UI", "Ошибка открытия LogViewerActivity", e)
            }
        }

        root.bindClickByNames("btnInfoHelp") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.infoHelpDialog.show()
            }
        }

        root.bindClickByNames("btnManageTemplates") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.templatesManagerDialog.show()
            }
        }

        root.bindClickByNames("btnExport", "btnImport") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.exportImportDialog.show()
            }
        }

        updateUIStatusIndicators()
    }

    override fun onResume() {
        super.onResume()
        updateUIStatusIndicators()
    }

    private fun openRestrictedSettingsMenu() {
        try {
            val intent = Intent(
                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:$packageName")
            )
            startActivity(intent)
            Toast.makeText(
                this,
                "Нажмите 3 точки в правом верхнем углу и выберите 'Разрешить ограниченные настройки'",
                Toast.LENGTH_LONG
            ).show()
            logDiagnostic("UI", "Открыто меню снятия ограничений Restricted Settings.")
        } catch (e: Exception) {
            logError("UI", "Ошибка открытия настроек приложения", e)
        }
    }

    private fun updateUIStatusIndicators() {
        val root = window.decorView.findViewById<View>(android.R.id.content)
        val isServiceActive = MyAutoClickService.instance != null
        val hasOverlay = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) Settings.canDrawOverlays(this) else true

        (root.findViewByNames("btnAccessibility") as? Button)?.apply {
            text = if (isServiceActive) "1. Accessibility: [ ВКЛ ]" else "1. Accessibility: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (isServiceActive) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnOverlay") as? Button)?.apply {
            text = if (hasOverlay) "2. Оверлеи: [ ВКЛ ]" else "2. Оверлеи: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (hasOverlay) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnPermissionsHelp", "btnAppDetails") as? Button)?.apply {
            text = "3. Снятие ограничений"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
        }
    }

    private fun initRepositories() {
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)
    }

    private fun initEngines() {
        actionEditorEngine = ActionEditorEngine()
    }
}
"""

print("=== НАЧАЛО ГЕНЕРАЦИИ AutoTap v40.0.0-PRO ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ГЕНЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА ===")