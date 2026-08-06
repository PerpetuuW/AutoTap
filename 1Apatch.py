import os
import sys
import xml.etree.ElementTree as ET

def validate_kotlin(content, filename):
    brackets = {'(': ')', '{': '}', '[': ']'}
    stack = []
    for char in content:
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

def validate_xml(content, filename):
    try:
        ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Ошибка синтаксиса XML в {filename}: {e}")

files = {}

# 1. AndroidManifest.xml
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

# 2. Accessibility Service Config XML
files["app/src/main/res/xml/accessibility_service_config.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeAllMask"
    android:accessibilityFeedbackType="feedbackGeneric"
    android:accessibilityFlags="flagDefault|flagIncludeNotImportantViews|flagRequestTouchExplorationMode"
    android:canPerformGestures="true"
    android:canRetrieveWindowContent="true"
    android:description="@string/app_name" />
"""

# 3. File Paths XML
files["app/src/main/res/xml/file_paths.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <external-path name="external_files" path="." />
    <files-path name="internal_files" path="." />
</paths>
"""

# 4. Themes XML
files["app/src/main/res/values/themes.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.AutoTap" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">#6200EE</item>
        <item name="colorPrimaryVariant">#3700B3</item>
        <item name="colorOnPrimary">#FFFFFF</item>
        <item name="colorSecondary">#03DAC6</item>
        <item name="colorSecondaryVariant">#018786</item>
        <item name="colorOnSecondary">#000000</item>
        <item name="android:statusBarColor">?attr/colorPrimaryVariant</item>
    </style>
</resources>
"""

# 5. Styles XML
files["app/src/main/res/values/styles.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Дополнительные стили элементов UI -->
</resources>
"""

# 6. Structured Logger c ротацией логов 512 КБ
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

# 7. Модель конфигурации шагов ActionConfig v35
files["app/src/main/java/com/example/autotap/model/ActionConfig.kt"] = """package com.example.autotap.model

import android.graphics.PointF

enum class ActionType {
    CLICK, SWIPE, LONG_PRESS, AI_SEARCH, WAIT, LOAD_SCRIPT
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

# 8. Ядро службы MyAutoClickService
files["app/src/main/java/com/example/autotap/MyAutoClickService.kt"] = """package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Bitmap
import android.graphics.PointF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.accessibility.AccessibilityEvent
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import java.util.concurrent.ConcurrentLinkedQueue

class MyAutoClickService : AccessibilityService() {

    companion object {
        @Volatile var instance: MyAutoClickService? = null
    }

    val actionsList = mutableListOf<ActionConfig>()
    @Volatile var isPlaying = false
    var globalClickDurationMs: Long = 50L

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
        logDiagnostic("OVERLAY", "MyAutoClickService инициализирован и подключен.")
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
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator ?: return
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
}
"""

# 9. MainActivity
files["app/src/main/java/com/example/autotap/MainActivity.kt"] = """package com.example.autotap

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        StructuredLogger.init(this)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        val statusText = TextView(this).apply {
            text = "AutoTap v35 System Status"
            textSize = 18f
        }
        layout.addView(statusText)

        val btnAccessibility = Button(this).apply {
            text = "Включить Accessibility Service"
            setOnClickListener {
                try {
                    startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                } catch (e: Exception) {
                    logError("UI", "Ошибка перехода в настройки Accessibility", e)
                }
            }
        }
        layout.addView(btnAccessibility)

        setContentView(layout)
        logDiagnostic("UI", "MainActivity успешно инициализирована.")
    }
}
"""

print("=== НАЧАЛО СОЗДАНИЯ МОДУЛЯ 1 (AutoTap v35) ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)
    elif rel_path.endswith(".xml"):
        validate_xml(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    if not os.path.exists(abs_path) or os.path.getsize(abs_path) == 0:
        raise RuntimeError(f"Файл {rel_path} не записан!")

    print(f"SUCCESS: {rel_path}")

print("=== МОДУЛЬ 1 УСПЕШНО СОЗДАН ===")