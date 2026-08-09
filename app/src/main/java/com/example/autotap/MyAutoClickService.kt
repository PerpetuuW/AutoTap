package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.content.res.Configuration
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorSpace
import android.graphics.PointF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Display
import android.view.accessibility.AccessibilityEvent
import android.widget.Toast
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

        logDiagnostic("OVERLAY", "MyAutoClickService полностью инициализирован.")
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        logDiagnostic("SYSTEM", "Смена конфигурации экрана (поворот / Fold).")
        if (::overlayManager.isInitialized) {
            overlayManager.onConfigurationChanged()
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

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
        if (::recordingEngine.isInitialized && recordingEngine.isRecording) {
            recordingEngine.recordClick(xNorm, yNorm)
        }
        logDiagnostic("SCRIPT", "Добавлено новое действие на позиции ($xNorm, $yNorm)")
    }

    fun getSafeScriptRepository(): ScriptRepository {
        return if (::scriptRepository.isInitialized) {
            scriptRepository
        } else {
            ScriptRepository(this).also { scriptRepository = it }
        }
    }

    fun getSafeTemplateRepository(): TemplateRepository {
        return if (::templateRepository.isInitialized) {
            templateRepository
        } else {
            TemplateRepository(this).also { templateRepository = it }
        }
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        getSafeScriptRepository().saveScript(name, actions)
    }

    fun loadScriptByName(name: String): Boolean {
        val loaded = getSafeScriptRepository().loadScript(name)
        if (loaded.isNotEmpty()) {
            actionsList.clear()
            actionsList.addAll(loaded)
            return true
        }
        return false
    }

    fun captureScreenBitmapAsync(callback: (Bitmap?) -> Unit) {
        val delayMs = globalPreScreenshotDelayMs.coerceAtLeast(250L)
        mainHandler.postDelayed({
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    takeScreenshot(
                        Display.DEFAULT_DISPLAY,
                        mainExecutor,
                        object : TakeScreenshotCallback {
                            override fun onSuccess(screenshotResult: ScreenshotResult) {
                                try {
                                    val buffer = screenshotResult.hardwareBuffer
                                    val cs = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                                        screenshotResult.colorSpace ?: ColorSpace.get(ColorSpace.Named.SRGB)
                                    } else null

                                    val hwBitmap = if (cs != null) {
                                        Bitmap.wrapHardwareBuffer(buffer, cs)
                                    } else {
                                        Bitmap.wrapHardwareBuffer(buffer, ColorSpace.get(ColorSpace.Named.SRGB))
                                    }

                                    val finalBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                                    buffer.close()

                                    if (finalBitmap != null) {
                                        logDiagnostic("AI_SCANNER", "Скриншот успешно снят (${finalBitmap.width}x${finalBitmap.height}px)")
                                        callback(finalBitmap)
                                    } else {
                                        callback(generateFallbackFrame())
                                    }
                                } catch (e: Exception) {
                                    logError("AI_SCANNER", "Ошибка обработки скриншота", e)
                                    callback(generateFallbackFrame())
                                }
                            }

                            override fun onFailure(errorCode: Int) {
                                logError("AI_SCANNER", "Ошибка takeScreenshot код: $errorCode", null)
                                callback(generateFallbackFrame())
                            }
                        }
                    )
                } catch (e: SecurityException) {
                    logError("AI_SCANNER", "SecurityException takeScreenshot: выключите и включите службу AutoTap в Спец. возможностях", e)
                    notifyUserToResetAccessibilitySwitch()
                    callback(generateFallbackFrame())
                } catch (e: Exception) {
                    logError("AI_SCANNER", "Ошибка вызова takeScreenshot API", e)
                    callback(generateFallbackFrame())
                }
            } else {
                callback(generateFallbackFrame())
            }
        }, delayMs)
    }

    private fun notifyUserToResetAccessibilitySwitch() {
        mainHandler.post {
            Toast.makeText(
                this,
                "⚠️ Перезапустите тумблер AutoTap в Спец. возможностях для активации скриншотов!",
                Toast.LENGTH_LONG
            ).show()
        }
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
        if (::overlayManager.isInitialized) overlayManager.showControlPanel()
    }

    fun hideControlPanel() {
        if (::overlayManager.isInitialized) overlayManager.hideControlPanel()
    }

    fun showFloatingStopButton() {
        if (::overlayManager.isInitialized) overlayManager.showFloatingStopButton()
    }

    fun hideFloatingStopButton() {
        if (::overlayManager.isInitialized) overlayManager.hideFloatingStopButton()
    }

    fun showClickVisualizer(x: Float, y: Float) {
        if (::overlayManager.isInitialized) overlayManager.showClickVisualizer(x, y)
    }
}
