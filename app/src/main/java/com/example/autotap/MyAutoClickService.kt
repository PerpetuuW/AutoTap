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
    var globalPreScreenshotDelayMs: Long = 50L

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

        logDiagnostic("SERVICE", "Служба Спец. возможностей подключена и инициализирована.")
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        logDiagnostic("SYSTEM", "Смена конфигурации экрана (поворот / ориентация).")
        if (::overlayManager.isInitialized) {
            overlayManager.onConfigurationChanged()
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {
        logError("SERVICE", "Служба Accessibility прервана системой.", null)
        gestureQueue.clear()
        isExecutingGesture = false
    }

    override fun onDestroy() {
        super.onDestroy()
        logDiagnostic("SERVICE", "Служба Accessibility уничтожена.")
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
                logDiagnostic("GESTURE", "Жест успешно выполнен: " + task.description)
                task.callback?.invoke(true)
                mainHandler.post { processNextGesture() }
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                isExecutingGesture = false
                logError("GESTURE", "Жест отменен системой: " + task.description, null)
                task.callback?.invoke(false)
                mainHandler.post { processNextGesture() }
            }
        }

        val dispatched = dispatchGesture(gesture, resultCallback, mainHandler)
        if (!dispatched) {
            isExecutingGesture = false
            logError("GESTURE", "Не удалось отправить жест в ОС: " + task.description, null)
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
        logDiagnostic("SCRIPT", "Добавлено новое действие на позиции (" + xNorm + ", " + yNorm + ")")
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

    // 💥 КРИТИЧЕСКИЙ ФИКС: Безопасное снятие скриншота без блокировки ERROR_SCREENSHOT_SECURE_WINDOW
    fun captureScreenBitmapAsync(callback: (Bitmap?) -> Unit) {
        logDiagnostic("SCREEN_CAPTURE", "Подготовка к снятию кадра... (Пауза: " + globalPreScreenshotDelayMs + "ms)")
        val takeAction = Runnable {
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

                                    val rawBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                                    buffer.close()

                                    if (rawBitmap != null) {
                                        val canonicalBitmap = Bitmap.createBitmap(rawBitmap.width, rawBitmap.height, Bitmap.Config.ARGB_8888)
                                        val canvas = Canvas(canonicalBitmap)
                                        canvas.drawBitmap(rawBitmap, 0f, 0f, null)
                                        rawBitmap.recycle()

                                        logDiagnostic("SCREEN_CAPTURE", "Скриншот успешно получен (" + canonicalBitmap.width + "x" + canonicalBitmap.height + "px)")
                                        callback(canonicalBitmap)
                                    } else {
                                        logError("SCREEN_CAPTURE", "Bitmap.wrapHardwareBuffer вернул NULL. Использование заглушки.", null)
                                        callback(generateFallbackFrame())
                                    }
                                } catch (e: Exception) {
                                    logError("SCREEN_CAPTURE", "Ошибка конвертации HardwareBuffer в Bitmap", e)
                                    callback(generateFallbackFrame())
                                }
                            }

                            override fun onFailure(errorCode: Int) {
                                val errorDetail = when (errorCode) {
                                    1 -> "ERROR_SCREENSHOT_INVALID_DISPLAY (1)"
                                    2 -> "ERROR_TAKE_SCREENSHOT_INTERNAL_ERROR (2)"
                                    3 -> "ERROR_SCREENSHOT_SECURE_WINDOW (3)"
                                    else -> "НЕИЗВЕСТНАЯ ОШИБКА (" + errorCode + ")"
                                }
                                logError("SCREEN_CAPTURE", "Сбой takeScreenshot(): " + errorDetail, null)
                                callback(generateFallbackFrame())
                            }
                        }
                    )
                } catch (e: SecurityException) {
                    logError("SCREEN_CAPTURE", "SecurityException: недостаточно прав для скриншота.", e)
                    notifyUserToResetAccessibilitySwitch()
                    callback(generateFallbackFrame())
                } catch (e: Exception) {
                    logError("SCREEN_CAPTURE", "Исключение при вызове takeScreenshot()", e)
                    callback(generateFallbackFrame())
                }
            } else {
                logError("SCREEN_CAPTURE", "Android API " + Build.VERSION.SDK_INT + " < 30 (Android 11). Скриншоты недоступны.", null)
                callback(generateFallbackFrame())
            }
        }

        if (globalPreScreenshotDelayMs > 0) {
            mainHandler.postDelayed(takeAction, globalPreScreenshotDelayMs)
        } else {
            mainHandler.post(takeAction)
        }
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
            val success = latch.await(3000, TimeUnit.MILLISECONDS)
            if (!success) {
                logError("SCREEN_CAPTURE", "Таймаут CountDownLatch (>3000ms) при ожидании скриншота!", null)
            }
        } catch (e: Exception) {
            logError("SCREEN_CAPTURE", "Прерывание ожидания CountDownLatch", e)
        }
        return result ?: generateFallbackFrame()
    }

    private fun generateFallbackFrame(): Bitmap {
        logError("SCREEN_CAPTURE", "[ВНИМАНИЕ] Сгенерирован фолбэк-кадр (400x600px). ИИ-поиск на таком кадре не даст совпадений!", null)
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
