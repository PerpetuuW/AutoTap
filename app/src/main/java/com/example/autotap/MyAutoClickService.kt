package com.example.autotap

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
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.GestureExecutor
import com.example.autotap.engine.ScriptExecutor
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

    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var scriptRepository: ScriptRepository
    lateinit var templateRepository: TemplateRepository
    lateinit var aiScannerEngine: AiScannerEngine

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
        scriptRepository = ScriptRepository(this)
        templateRepository = TemplateRepository(this)
        aiScannerEngine = AiScannerEngine(this)

        logDiagnostic("OVERLAY", "MyAutoClickService и AiScannerEngine полностью инициализированы (Модуль 3).")
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

    fun addNewActionAtPosition(xNorm: Float, yNorm: Float) {
        actionsList.add(ActionConfig(xNorm = xNorm, yNorm = yNorm))
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

    fun captureScreenBitmap(): Bitmap? {
        return null
    }

    fun showControlPanel() {
        logDiagnostic("OVERLAY", "Запрос показа ControlPanel")
    }

    fun hideControlPanel() {
        logDiagnostic("OVERLAY", "Запрос скрытия ControlPanel")
    }

    fun showFloatingStopButton() {
        logDiagnostic("OVERLAY", "Запрос показа кнопки СТОП")
    }

    fun hideFloatingStopButton() {
        logDiagnostic("OVERLAY", "Запрос скрытия кнопки СТОП")
    }

    fun showClickVisualizer(x: Float, y: Float) {
        logDiagnostic("OVERLAY", "Визуализация клика в ($x, $y)")
    }
}
