package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityService.ScreenshotResult
import android.accessibilityservice.AccessibilityService.TakeScreenshotCallback
import android.accessibilityservice.GestureDescription
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.Rect
import android.graphics.Typeface
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.ContextThemeWrapper
import android.view.Display
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.io.PrintWriter
import java.lang.ref.WeakReference
import java.text.SimpleDateFormat
import java.util.Date
import java.util.HashSet
import java.util.Locale
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executor
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.min

@Suppress("SpellCheckingInspection", "AccessibilityPolicy", "DEPRECATION", "ClickableViewAccessibility")
@SuppressLint("InflateParams", "SetTextI18n")
class MyAutoClickService : AccessibilityService() {

    private lateinit var windowManager: WindowManager
    private var controlPanelView: View? = null
    private var floatingStopView: View? = null
    private var candidateSelectionOverlayView: View? = null
    private var captureFrameView: View? = null
    private var highlightOverlayView: View? = null
    private var recordOverlayView: View? = null
    private var recordBarView: View? = null
    private var joystickOverlayView: View? = null
    private var visualizerOverlay: View? = null
    private var searchHintView: TextView? = null

    private var tutorialCardView: View? = null
    private var currentTutorialStep = 0
    private var isTutorialActive = false
    private var btnCaptureAnimator: android.animation.ObjectAnimator? = null

    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false

    val globalTemplates = ArrayList<Bitmap>()
    val globalTemplatesNames = ArrayList<String>()

    private var isNumbersHidden = false
    var isRecording = false
    private var isInjectingGesture = false
    private var lastRecordedTime = 0L

    var globalClickDurationMs: Long = 120L
    var globalSwipeDurationMs: Long = 300L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = true
    var globalRelayNextScript: String = ""

    private val uiExecutor = Executor { command ->
        Handler(Looper.getMainLooper()).post(command)
    }

    private val bgScannerExecutor = Executors.newSingleThreadExecutor()
    private val highlightHandler = Handler(Looper.getMainLooper())
    private val hideHighlightRunnable = Runnable { removeHighlightOverlay() }

    private var highlightedButtonAnim: android.animation.ObjectAnimator? = null
    private var isCalibrationCancelled = false

    companion object {
        private var serviceRef: WeakReference<MyAutoClickService>? = null
        private val logLock = Any()

        @JvmStatic
        var instance: MyAutoClickService?
            get() = serviceRef?.get()
            set(value) {
                serviceRef = if (value != null) WeakReference(value) else null
            }

        @JvmStatic
        fun logError(context: Context, e: Throwable) {
            android.util.Log.e("AutoTap", "Caught Exception", e)
            synchronized(logLock) {
                try {
                    val logFile = File(context.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("=== ${sdf.format(Date())} ===")
                        e.printStackTrace(writer)
                        writer.println()
                        writer.flush()
                    }
                } catch (_: Exception) {
                }
            }
        }

        @JvmStatic
        fun logAppEvent(context: Context, tag: String, message: String) {
            android.util.Log.d("AutoTap", "[$tag] $message")
            synchronized(logLock) {
                try {
                    val logFile = File(context.filesDir, "error_log.txt")
                    if (logFile.exists() && logFile.length() > 512 * 1024) {
                        val tailContent = logFile.readText().takeLast(256 * 1024)
                        logFile.writeText("...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + tailContent)
                    }

                    FileOutputStream(logFile, true).use { out ->
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())
                        val writer = PrintWriter(out)
                        writer.println("[${sdf.format(Date())}][$tag] $message")
                        writer.flush()
                    }
                } catch (_: Exception) {
                }
            }
        }
    }

    fun showClickVisualizer(x: Float, y: Float) {
        uiExecutor.execute {
            if (visualizerOverlay == null) {
                visualizerOverlay =
                    View(this).apply { background = getDrawable(R.drawable.circle_target) }
                val params = WindowManager.LayoutParams(
                    dpToPx(40), dpToPx(40), getOverlayType(),
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                    PixelFormat.TRANSLUCENT
                )
                safeAddView(visualizerOverlay, params)
            }

            val params = visualizerOverlay?.layoutParams as? WindowManager.LayoutParams
            if (params != null) {
                params.x = (x - dpToPx(20)).toInt()
                params.y = (y - dpToPx(20)).toInt()
                safeUpdateViewLayout(visualizerOverlay, params)

                visualizerOverlay?.alpha = 1f
                visualizerOverlay?.scaleX = 0.5f
                visualizerOverlay?.scaleY = 0.5f

                visualizerOverlay?.animate()
                    ?.scaleX(2.0f)?.scaleY(2.0f)?.alpha(0f)
                    ?.setDuration(300)?.start()
            }
        }
    }

    private fun showAiSearchHint(stepId: Int) {
        if (searchHintView == null) {
            searchHintView = TextView(this).apply {
                text = "🔍 Шаг #$stepId: ИИ сканирует экран..."
                setTextColor(Color.parseColor("#FFB703"))
                textSize = 12f
                setTypeface(null, Typeface.BOLD)
                setBackgroundResource(R.drawable.drag_handle_bg)
                setPadding(dpToPx(16), dpToPx(8), dpToPx(16), dpToPx(8))
            }
            val params = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
                getOverlayType(),
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                y = dpToPx(50)
            }
            safeAddView(searchHintView, params)
        } else {
            searchHintView?.text = "🔍 Шаг #$stepId: ИИ сканирует экран..."
            searchHintView?.visibility = View.VISIBLE
        }
    }

    private fun hideAiSearchHint() {
        searchHintView?.visibility = View.GONE
    }

    private fun getTemplateMetadataFile(maskPath: String): File {
        val maskFile = File(maskPath)
        val parent = maskFile.parentFile ?: filesDir
        val name = maskFile.nameWithoutExtension
        return File(parent, "${name}.json")
    }

    private fun playMatchNotification() {
        try {
            vibrateFeedback(150L)
            val toneGen =
                android.media.ToneGenerator(android.media.AudioManager.STREAM_NOTIFICATION, 80)
            toneGen.startTone(android.media.ToneGenerator.TONE_PROP_BEEP, 200)
            Handler(Looper.getMainLooper()).postDelayed({
                try {
                    toneGen.release()
                } catch (_: Exception) {
                }
            }, 300L)
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun showScriptPickerDialog(titleText: String, onScriptSelected: (String) -> Unit) {
        val dir = File(filesDir, "scripts")
        val scriptFiles = dir.listFiles()?.filter { it.name.endsWith(".json") } ?: emptyList()

        val dialogView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#161B22"))
            setPadding(dpToPx(14), dpToPx(14), dpToPx(14), dpToPx(14))
        }

        val tvTitle = TextView(this).apply {
            text = titleText
            setTextColor(Color.WHITE)
            textSize = 14f
            setTypeface(null, Typeface.BOLD)
            setPadding(0, 0, 0, dpToPx(10))
        }
        dialogView.addView(tvTitle)

        val listLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }

        val btnNone = Button(this).apply {
            text = "❌ Нет / Очистить"
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.parseColor("#21262D"))
            textSize = 11f
            setOnClickListener {
                safeRemoveView(dialogView)
                onScriptSelected("")
            }
        }
        listLayout.addView(btnNone)

        for (file in scriptFiles) {
            val name = file.nameWithoutExtension
            val btnSc = Button(this).apply {
                text = "📁 $name"
                setTextColor(Color.WHITE)
                backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
                textSize = 11f
                val lp =
                    LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dpToPx(38))
                lp.topMargin = dpToPx(4)
                layoutParams = lp
                setOnClickListener {
                    safeRemoveView(dialogView)
                    onScriptSelected(name)
                }
            }
            listLayout.addView(btnSc)
        }

        val scroll = android.widget.ScrollView(this).apply {
            layoutParams =
                LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dpToPx(220))
            addView(listLayout)
        }
        dialogView.addView(scroll)

        val btnClose = Button(this).apply {
            text = "Отмена"
            backgroundTintList = ColorStateList.valueOf(Color.parseColor("#F04438"))
            setOnClickListener { safeRemoveView(dialogView) }
        }
        dialogView.addView(btnClose)

        val params = WindowManager.LayoutParams(
            dpToPx(280),
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.CENTER }

        safeAddView(dialogView, params)
    }

    private fun showMultiTemplateSelectorDialog(config: ActionConfig, onUpdated: () -> Unit) {
        if (globalTemplatesNames.isEmpty()) {
            Toast.makeText(this, "Пул шаблонов пуст! Сделайте снимки 📸", Toast.LENGTH_SHORT).show()
            return
        }

        val dialogView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#161B22"))
            setPadding(dpToPx(14), dpToPx(14), dpToPx(14), dpToPx(14))
        }

        val tvTitle = TextView(this).apply {
            text = "🗂 Выбор Мультишаблонов"
            setTextColor(Color.WHITE)
            textSize = 15f
            setTypeface(null, Typeface.BOLD)
        }
        dialogView.addView(tvTitle)

        val tvSub = TextView(this).apply {
            text = "Кликер находит и нажимает любой из выбранных шаблонов при появлении"
            setTextColor(Color.parseColor("#58A6FF"))
            textSize = 10f
            setPadding(0, 0, 0, dpToPx(8))
        }
        dialogView.addView(tvSub)

        val btnRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 0, 0, dpToPx(8))

            val btnSelectAll = Button(this@MyAutoClickService).apply {
                text = "✅ Выбрать всё"
                textSize = 10f
                backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
                layoutParams = LinearLayout.LayoutParams(0, dpToPx(36), 1.0f)
            }
            val btnDeselectAll = Button(this@MyAutoClickService).apply {
                text = "❌ Снять выбор"
                textSize = 10f
                backgroundTintList = ColorStateList.valueOf(Color.parseColor("#21262D"))
                layoutParams =
                    LinearLayout.LayoutParams(0, dpToPx(36), 1.0f).apply { leftMargin = dpToPx(4) }
            }
            addView(btnSelectAll)
            addView(btnDeselectAll)
        }
        dialogView.addView(btnRow)

        val listLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }

        fun refreshList() {
            listLayout.removeAllViews()

            for (i in globalTemplatesNames.indices) {
                val path = globalTemplatesNames[i]
                val fName = File(path).nameWithoutExtension

                val itemRow = LinearLayout(this@MyAutoClickService).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                    setPadding(0, dpToPx(4), 0, dpToPx(4))

                    val ivPrev = ImageView(this@MyAutoClickService).apply {
                        val bmp = globalTemplates.getOrNull(i) ?: BitmapFactory.decodeFile(path)
                        setImageBitmap(bmp)
                        scaleType = ImageView.ScaleType.FIT_CENTER
                        layoutParams = LinearLayout.LayoutParams(dpToPx(36), dpToPx(36))
                        setBackgroundColor(Color.parseColor("#3A4763"))
                    }
                    addView(ivPrev)

                    val tvName = TextView(this@MyAutoClickService).apply {
                        text = " №${i + 1}: $fName"
                        setTextColor(Color.WHITE)
                        textSize = 11f
                        layoutParams = LinearLayout.LayoutParams(
                            0,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                            1.0f
                        )
                    }
                    addView(tvName)

                    val cb = android.widget.CheckBox(this@MyAutoClickService).apply {
                        isChecked = config.multiTemplateIndices.contains(i)
                        setOnCheckedChangeListener { _, isChecked ->
                            if (isChecked) {
                                if (!config.multiTemplateIndices.contains(i)) config.multiTemplateIndices.add(i)
                            } else {
                                config.multiTemplateIndices.remove(i)
                            }
                        }
                    }
                    addView(cb)
                }
                listLayout.addView(itemRow)
            }
        }
        refreshList()

        val btnSelectAll = (btnRow.getChildAt(0) as Button)
        val btnDeselectAll = (btnRow.getChildAt(1) as Button)

        btnSelectAll.setOnClickListener {
            config.multiTemplateIndices.clear()
            for (i in globalTemplatesNames.indices) config.multiTemplateIndices.add(i)
            refreshList()
        }

        btnDeselectAll.setOnClickListener {
            config.multiTemplateIndices.clear()
            refreshList()
        }

        val scroll = android.widget.ScrollView(this).apply {
            layoutParams =
                LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dpToPx(240))
            addView(listLayout)
        }
        dialogView.addView(scroll)

        val params = WindowManager.LayoutParams(
            dpToPx(300),
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.CENTER }

        val btnDone = Button(this).apply {
            text = "Готово"
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            setOnClickListener {
                safeRemoveView(dialogView)
                onUpdated()
            }
        }
        dialogView.addView(btnDone)

        safeAddView(dialogView, params)
    }

    fun vibrateFeedback(durationMs: Long = 25L) {
        try {
            val vibrator = getSystemService(VIBRATOR_SERVICE) as? Vibrator
            if (vibrator != null && vibrator.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(
                        VibrationEffect.createOneShot(
                            durationMs,
                            VibrationEffect.DEFAULT_AMPLITUDE
                        )
                    )
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (_: Exception) {
        }
    }

    private fun removeCandidateSelectionOverlay() {
        if (candidateSelectionOverlayView != null) {
            safeRemoveView(candidateSelectionOverlayView)
            candidateSelectionOverlayView = null
        }
    }

    fun removeHighlightOverlay() {
        highlightHandler.removeCallbacks(hideHighlightRunnable)
        if (highlightOverlayView != null) {
            safeRemoveView(highlightOverlayView)
            highlightOverlayView = null
        }
    }

    private fun setTargetsTouchable(touchable: Boolean) {
        for (action in actionsList) {
            val params = action.startView.layoutParams as? WindowManager.LayoutParams ?: continue
            if (touchable) {
                params.flags = params.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
            } else {
                params.flags = params.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
            }
            safeUpdateViewLayout(action.startView, params)

            action.endView?.let { endView ->
                val endParams = endView.layoutParams as? WindowManager.LayoutParams ?: return@let
                if (touchable) {
                    endParams.flags =
                        endParams.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
                } else {
                    endParams.flags =
                        endParams.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                }
                safeUpdateViewLayout(endView, endParams)
            }
        }
    }

    fun showJoystickManipulator() {
        if (joystickOverlayView != null) {
            joystickOverlayView?.visibility = View.VISIBLE
            return
        }

        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        joystickOverlayView = LayoutInflater.from(contextThemeWrapper)
            .inflate(R.layout.floating_joystick_control, null)

        val displayMetrics = resources.displayMetrics
        val screenW = displayMetrics.widthPixels
        val screenH = displayMetrics.heightPixels

        val sizePx = dpToPx(160)
        val params = WindowManager.LayoutParams(
            sizePx,
            sizePx + dpToPx(40),
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = dpToPx(30)
            y = screenH / 2 - sizePx / 2
        }

        val handleMove = joystickOverlayView!!.findViewById<View>(R.id.handleMoveJoystick)
        val btnClose = joystickOverlayView!!.findViewById<View>(R.id.btnCloseJoystick)
        val btnRecordJoystick = joystickOverlayView!!.findViewById<Button>(R.id.btnRecordJoystick)
        val viewKnob = joystickOverlayView!!.findViewById<View>(R.id.viewJoystickKnob)

        var isJoystickRecording = false
        var joystickStartTime = 0L
        var startX = 0f
        var startY = 0f

        val dragFrameListener = object : View.OnTouchListener {
            private var initX = 0
            private var initY = 0
            private var touchX = 0f
            private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x
                        initY = params.y
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        params.x =
                            (initX + (event.rawX - touchX).toInt()).coerceIn(0, screenW - sizePx)
                        params.y =
                            (initY + (event.rawY - touchY).toInt()).coerceIn(0, screenH - sizePx)
                        safeUpdateViewLayout(joystickOverlayView, params)
                        return true
                    }
                }
                return false
            }
        }
        handleMove?.setOnTouchListener(dragFrameListener)

        viewKnob?.isClickable = false
        viewKnob?.isFocusable = false

        viewKnob?.setOnTouchListener(object : View.OnTouchListener {
            private var maxRadiusPx = dpToPx(50).toFloat()

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        startX = event.rawX
                        startY = event.rawY
                        joystickStartTime = System.currentTimeMillis()
                        vibrateFeedback(20L)
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        val dx = event.rawX - startX
                        val dy = event.rawY - startY
                        val dist = hypot(dx.toDouble(), dy.toDouble()).toFloat()

                        val angle = Math.atan2(dy.toDouble(), dx.toDouble())
                        val clampedDist = min(dist, maxRadiusPx)

                        val knobX = (clampedDist * Math.cos(angle)).toFloat()
                        val knobY = (clampedDist * Math.sin(angle)).toFloat()

                        viewKnob.translationX = knobX
                        viewKnob.translationY = knobY
                        return true
                    }

                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        val duration =
                            (System.currentTimeMillis() - joystickStartTime).coerceIn(100L, 5000L)
                        val finalDx = viewKnob.translationX
                        val finalDy = viewKnob.translationY
                        val finalDist = hypot(finalDx.toDouble(), finalDy.toDouble()).toFloat()

                        viewKnob.animate().translationX(0f).translationY(0f).setDuration(180)
                            .start()

                        if (finalDist > 15) {
                            val centerX = params.x + sizePx / 2f
                            val centerY = params.y + dpToPx(30) + sizePx / 2f
                            val targetX = centerX + finalDx
                            val targetY = centerY + finalDy

                            performSwipe(centerX, centerY, targetX, targetY, duration)

                            if (isJoystickRecording) {
                                addNewActionAtPosition(centerX, centerY, 500L, ActionType.SWIPE, -1)
                                val cfg = actionsList.last()
                                cfg.holdDuration = duration
                                spawnEndTargetAtPosition(cfg, targetX, targetY)
                                Toast.makeText(
                                    this@MyAutoClickService,
                                    "🕹 Записано движение джойстика (${duration}мс)!",
                                    Toast.LENGTH_SHORT
                                ).show()
                            }
                        }
                        return true
                    }
                }
                return false
            }
        })

        btnRecordJoystick?.setOnClickListener {
            vibrateFeedback(25L)
            isJoystickRecording = !isJoystickRecording
            btnRecordJoystick.text = if (isJoystickRecording) "🔴 Запись..." else "⏺ ЗАПИСАТЬ"
            btnRecordJoystick.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isJoystickRecording) R.color.red_close else R.color.accent_blue))

            if (isJoystickRecording) {
                isRecording = true
                actionsList.forEach { act ->
                    act.startView.visibility = View.INVISIBLE
                    act.endView?.visibility = View.INVISIBLE
                }
                controlPanelView?.visibility = View.GONE
                showFloatingStopButton()
            } else {
                stopOverlayRecording()
            }
        }

        btnClose?.setOnClickListener {
            vibrateFeedback(25L)
            safeRemoveView(joystickOverlayView)
            joystickOverlayView = null
        }

        safeAddView(joystickOverlayView, params)
    }

    fun showGlobalSettingsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_global_settings, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
            dimAmount = 0.5f
        }

        val etClickDur = dialogView.findViewById<EditText>(R.id.etGlobalClickDuration)
        val etSwipeDur = dialogView.findViewById<EditText>(R.id.etGlobalSwipeDuration)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSaveGlobalSettings)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelGlobalSettings)

        etClickDur?.setText(globalClickDurationMs.toString())
        etSwipeDur?.setText(globalSwipeDurationMs.toString())

        btnSave?.setOnClickListener {
            vibrateFeedback(25L)
            globalClickDurationMs =
                etClickDur?.text?.toString()?.toLongOrNull()?.coerceIn(10L, 5000L) ?: 120L
            globalSwipeDurationMs =
                etSwipeDur?.text?.toString()?.toLongOrNull()?.coerceIn(50L, 10000L) ?: 300L
            Toast.makeText(this, "Глобальные настройки сохранены!", Toast.LENGTH_SHORT).show()
            safeRemoveView(dialogView)
        }

        btnCancel?.setOnClickListener {
            vibrateFeedback(20L)
            safeRemoveView(dialogView)
        }

        safeAddView(dialogView, params)
    }

    private fun showEditDialog(config: ActionConfig) {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.floating_edit_dialog, null)
        val currentStepIdx = actionsList.indexOf(config)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
            softInputMode =
                WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE or WindowManager.LayoutParams.SOFT_INPUT_STATE_HIDDEN
        }

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val btnPrevStep = dialogView.findViewById<Button>(R.id.btnPrevStep)
        val btnNextStep = dialogView.findViewById<Button>(R.id.btnNextStep)

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val etStepOrder = dialogView.findViewById<EditText>(R.id.etStepOrder)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etRepeatCount = dialogView.findViewById<EditText>(R.id.etRepeatCount)
        val etRandomRadius = dialogView.findViewById<EditText>(R.id.etRandomRadius)
        val tvHoldTitle = dialogView.findViewById<TextView>(R.id.tvHoldTitle)
        val etHoldDuration = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val tvTemplateIndex = dialogView.findViewById<TextView>(R.id.tvTemplateIndex)
        val ivTemplatePreview =
            dialogView.findViewById<ImageView>(R.id.ivSelectedTemplateImagePreview)
        val btnPrevTemplate = dialogView.findViewById<Button>(R.id.btnPrevTemplate)
        val btnNextTemplate = dialogView.findViewById<Button>(R.id.btnNextTemplate)

        val btnCloneAction = dialogView.findViewById<Button>(R.id.btnCloneAction)
        val btnDeleteAction = dialogView.findViewById<Button>(R.id.btnDeleteAction)
        val btnSaveHeader = dialogView.findViewById<View>(R.id.btnSaveHeader)
        val btnCloseHeader = dialogView.findViewById<View>(R.id.btnCloseHeader)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSave)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        tvTitle?.text = "Действие #${config.id}"
        etStepOrder?.setText(config.id.toString())
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeatCount?.setText(if (config.repeatCount == -1) "∞" else config.repeatCount.toString())
        etRandomRadius?.setText(config.randomRadius.toString())
        etHoldDuration?.setText(config.holdDuration.toString())

        val etSimPct = dialogView.findViewById<EditText>(R.id.etSimilarityPercent)
        etSimPct?.setText(config.similarityPercent.toString())

        val etInterval = dialogView.findViewById<EditText>(R.id.etScanInterval)
        etInterval?.setText(config.scanIntervalSeconds.toString())

        val etPostDelay = dialogView.findViewById<EditText>(R.id.etPostMatchDelay)
        etPostDelay?.setText(config.postMatchDelaySeconds.toString())

        var selectedType = config.type

        fun updateTemplatePreviewUI() {
            if (globalTemplatesNames.isEmpty()) {
                tvTemplateIndex?.text = "Шаблонов нет (0)"
                ivTemplatePreview?.setImageBitmap(null)
                config.selectedTemplateIndex = -1
                return
            }

            if (config.selectedTemplateIndex !in globalTemplatesNames.indices) {
                config.selectedTemplateIndex = 0
            }

            val idx = config.selectedTemplateIndex
            val total = globalTemplatesNames.size
            val maskPath = globalTemplatesNames[idx]
            val fileName = File(maskPath).nameWithoutExtension

            tvTemplateIndex?.text = "№${idx + 1}/$total: $fileName"

            ivTemplatePreview?.setBackgroundColor(Color.parseColor("#3A4763"))
            val bmp = globalTemplates.getOrNull(idx) ?: BitmapFactory.decodeFile(maskPath)
            ivTemplatePreview?.setImageBitmap(bmp)
        }

        fun updateUI() {
            val isClick = selectedType == ActionType.CLICK
            val isHold = selectedType == ActionType.LONG_PRESS
            val isSwipe = selectedType == ActionType.SWIPE
            val isTrigger = selectedType == ActionType.TRIGGER

            btnTypeClick?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isClick) R.color.accent_blue else R.color.panel_blue))
            btnTypeClick?.setTextColor(if (isClick) Color.WHITE else Color.parseColor("#8B949E"))

            btnTypeHold?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isHold) R.color.accent_blue else R.color.panel_blue))
            btnTypeHold?.setTextColor(if (isHold) Color.WHITE else Color.parseColor("#8B949E"))

            btnTypeSwipe?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isSwipe) R.color.accent_blue else R.color.panel_blue))
            btnTypeSwipe?.setTextColor(if (isSwipe) Color.WHITE else Color.parseColor("#8B949E"))

            btnTypeTrigger?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isTrigger) R.color.accent_blue else R.color.panel_blue))
            btnTypeTrigger?.setTextColor(if (isTrigger) Color.WHITE else Color.parseColor("#8B949E"))

            tvHoldTitle?.visibility = if (isHold) View.VISIBLE else View.GONE
            etHoldDuration?.visibility = if (isHold) View.VISIBLE else View.GONE

            val layoutAiBlock = dialogView.findViewById<View>(R.id.layoutAiParametersBlock)
            layoutAiBlock?.visibility = if (isTrigger) View.VISIBLE else View.GONE

            val tvAiTimeoutTitle = dialogView.findViewById<TextView>(R.id.tvAiTimeoutTitle)
            val etAiTimeout = dialogView.findViewById<EditText>(R.id.etAiTimeout)
            tvAiTimeoutTitle?.visibility = if (isTrigger) View.VISIBLE else View.GONE
            etAiTimeout?.visibility = if (isTrigger) View.VISIBLE else View.GONE
            etAiTimeout?.setText(config.aiTimeoutSeconds.toString())

            val btnAiNotif = dialogView.findViewById<Button>(R.id.btnToggleAiNotification)
            btnAiNotif?.text =
                if (config.playAudioOnMatch) "🔔 Звук / Вибро при совпадении: [ВКЛ]" else "🔔 Звук / Вибро при совпадении: [ВЫКЛ]"
            btnAiNotif?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (config.playAudioOnMatch) R.color.accent_blue else R.color.panel_blue))

            val btnMulti = dialogView.findViewById<Button>(R.id.btnManageMultiTemplates)
            val multiCount = config.multiTemplateIndices.size
            btnMulti?.text =
                if (multiCount > 0) "🗂 Мультишаблоны: [ Выбрано $multiCount маск ]" else "🗂 Мультишаблоны: [ Обычный режим (1 маска) ]"
            btnMulti?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (multiCount > 0) R.color.accent_blue else R.color.panel_blue))

            val btnClickTarget = dialogView.findViewById<Button>(R.id.btnToggleClickTarget)
            btnClickTarget?.text =
                if (config.clickAiTarget) "🎯 Клик по мишени: [ВКЛ]" else "🎯 Клик по мишени: [ВЫКЛ]"
            btnClickTarget?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (config.clickAiTarget) R.color.accent_blue else R.color.panel_blue))

            val etJumpStep = dialogView.findViewById<EditText>(R.id.etJumpToStep)
            etJumpStep?.setText(config.jumpToStepOnMatch.toString())

            val btnScriptLoad = dialogView.findViewById<Button>(R.id.btnSelectScriptToLoad)
            btnScriptLoad?.text =
                if (config.targetScriptToLoad.isNotEmpty()) "📁 Переход на сценарий: [ ${config.targetScriptToLoad} ]" else "📁 Переход на сценарий: [ НЕТ ]"
            btnScriptLoad?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (config.targetScriptToLoad.isNotEmpty()) R.color.accent_blue else R.color.panel_blue))

            if (isTrigger) {
                updateTemplatePreviewUI()
            }
        }

        val btnClickTarget = dialogView.findViewById<Button>(R.id.btnToggleClickTarget)
        btnClickTarget?.setOnClickListener {
            vibrateFeedback(20L)
            config.clickAiTarget = !config.clickAiTarget
            updateUI()
        }

        val btnAiNotif = dialogView.findViewById<Button>(R.id.btnToggleAiNotification)
        btnAiNotif?.setOnClickListener {
            vibrateFeedback(20L)
            config.playAudioOnMatch = !config.playAudioOnMatch
            updateUI()
        }

        val btnMulti = dialogView.findViewById<Button>(R.id.btnManageMultiTemplates)
        btnMulti?.setOnClickListener {
            vibrateFeedback(20L)
            showMultiTemplateSelectorDialog(config) {
                updateUI()
            }
        }

        val btnScriptLoad = dialogView.findViewById<Button>(R.id.btnSelectScriptToLoad)
        btnScriptLoad?.setOnClickListener {
            vibrateFeedback(20L)
            showScriptPickerDialog("Выберите сценарий для перехода") { name ->
                config.targetScriptToLoad = name
                updateUI()
            }
        }

        val btnDelTemplate = dialogView.findViewById<Button>(R.id.btnDeleteSelectedTemplate)
        btnDelTemplate?.setOnClickListener {
            vibrateFeedback(30L)
            if (config.selectedTemplateIndex in globalTemplatesNames.indices) {
                moveTemplateToTrash(config.selectedTemplateIndex)
                loadAllTemplatesFromDisk()
                updateTemplatePreviewUI()
                updateUI()
            }
        }

        updateUI()

        btnPrevTemplate?.setOnClickListener {
            vibrateFeedback(20L)
            if (globalTemplatesNames.isNotEmpty()) {
                config.selectedTemplateIndex =
                    (config.selectedTemplateIndex - 1 + globalTemplatesNames.size) % globalTemplatesNames.size
                updateTemplatePreviewUI()
            }
        }

        btnNextTemplate?.setOnClickListener {
            vibrateFeedback(20L)
            if (globalTemplatesNames.isNotEmpty()) {
                config.selectedTemplateIndex =
                    (config.selectedTemplateIndex + 1) % globalTemplatesNames.size
                updateTemplatePreviewUI()
            }
        }

        btnTypeClick?.setOnClickListener { selectedType = ActionType.CLICK; updateUI() }
        btnTypeHold?.setOnClickListener { selectedType = ActionType.LONG_PRESS; updateUI() }
        btnTypeSwipe?.setOnClickListener { selectedType = ActionType.SWIPE; updateUI() }
        btnTypeTrigger?.setOnClickListener { selectedType = ActionType.TRIGGER; updateUI() }

        fun saveCurrentStepData() {
            config.type = selectedType
            val delaySec = etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0
            config.delay = (delaySec * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount =
                etRepeatCount?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius =
                etRandomRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration =
                etHoldDuration?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L

            val etAiTimeout = dialogView.findViewById<EditText>(R.id.etAiTimeout)
            config.aiTimeoutSeconds =
                etAiTimeout?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 15

            val etSimPctVal = dialogView.findViewById<EditText>(R.id.etSimilarityPercent)
            config.similarityPercent =
                etSimPctVal?.text?.toString()?.toIntOrNull()?.coerceIn(10, 99) ?: 70

            val etInterval = dialogView.findViewById<EditText>(R.id.etScanInterval)
            config.scanIntervalSeconds =
                etInterval?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 5

            val etPostDelay = dialogView.findViewById<EditText>(R.id.etPostMatchDelay)
            config.postMatchDelaySeconds =
                etPostDelay?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 3

            val etJumpStep = dialogView.findViewById<EditText>(R.id.etJumpToStep)
            config.jumpToStepOnMatch = etJumpStep?.text?.toString()?.toIntOrNull() ?: -1

            if (selectedType == ActionType.SWIPE && config.endView == null) {
                val loc = IntArray(2)
                config.startView.getLocationOnScreen(loc)
                spawnEndTargetAtPosition(
                    config,
                    loc[0].toFloat() + dpToPx(80),
                    loc[1].toFloat() + dpToPx(80)
                )
            } else if (selectedType != ActionType.SWIPE && config.endView != null) {
                safeRemoveView(config.endView)
                config.endView = null
            }
        }

        val btnCalibrateMatchesOnScreen =
            dialogView.findViewById<Button>(R.id.btnCalibrateMatchesOnScreen)
        btnCalibrateMatchesOnScreen?.setOnClickListener {
            vibrateFeedback(30L)
            saveCurrentStepData()
            safeRemoveView(dialogView)
            startTemplateCalibration(config)
        }

        btnCloneAction?.setOnClickListener {
            vibrateFeedback(25L)
            saveCurrentStepData()
            safeRemoveView(dialogView)

            val loc = IntArray(2)
            config.startView.getLocationOnScreen(loc)
            addNewActionAtPosition(
                loc[0].toFloat() + dpToPx(20),
                loc[1].toFloat() + dpToPx(20),
                config.delay,
                config.type,
                config.selectedTemplateIndex
            )
            Toast.makeText(this, "📋 Шаг #${config.id} успешно клонирован!", Toast.LENGTH_SHORT)
                .show()
        }

        btnDeleteAction?.setOnClickListener {
            vibrateFeedback(30L)
            safeRemoveView(dialogView)
            safeRemoveView(config.startView)
            config.endView?.let { safeRemoveView(it) }
            actionsList.remove(config)

            for (i in actionsList.indices) {
                val act = actionsList[i]
                act.id = i + 1
                act.startView.findViewById<TextView>(R.id.tvTargetNumber)?.text = act.id.toString()
                act.endView?.findViewById<TextView>(R.id.tvTargetNumberEnd)?.text = "${act.id}E"
            }
            Toast.makeText(this, "🗑 Шаг удален", Toast.LENGTH_SHORT).show()
        }

        btnPrevStep?.setOnClickListener {
            saveCurrentStepData()
            safeRemoveView(dialogView)
            if (currentStepIdx > 0) showEditDialog(actionsList[currentStepIdx - 1])
        }

        btnNextStep?.setOnClickListener {
            saveCurrentStepData()
            safeRemoveView(dialogView)
            if (currentStepIdx < actionsList.size - 1) showEditDialog(actionsList[currentStepIdx + 1])
        }

        val performSave = {
            vibrateFeedback(30L)
            saveCurrentStepData()
            safeRemoveView(dialogView)
            Toast.makeText(this, "Параметры шага #${config.id} сохранены!", Toast.LENGTH_SHORT)
                .show()
        }

        val performClose = {
            vibrateFeedback(25L)
            safeRemoveView(dialogView)
        }

        btnSaveHeader?.setOnClickListener { performSave() }
        btnCloseHeader?.setOnClickListener { performClose() }
        btnSave?.setOnClickListener { performSave() }
        btnCancel?.setOnClickListener { performClose() }

        safeAddView(dialogView, params)
    }

    fun showScriptsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_scripts, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
            dimAmount = 0.5f
        }

        val etScriptName = dialogView.findViewById<EditText>(R.id.etScriptName)
        val btnSaveScriptAction = dialogView.findViewById<Button>(R.id.btnSaveScriptAction)
        val layoutScriptsList = dialogView.findViewById<LinearLayout>(R.id.layoutScriptsList)
        val btnCloseScripts = dialogView.findViewById<Button>(R.id.btnCloseScripts)
        val btnCloseScriptsHeader = dialogView.findViewById<ImageButton>(R.id.btnCloseScriptsHeader)
        btnCloseScriptsHeader?.setOnClickListener { safeRemoveView(dialogView) }

        fun refreshScriptsList() {
            layoutScriptsList?.removeAllViews()
            val dir = File(filesDir, "scripts")
            if (dir.exists()) {
                dir.listFiles()?.forEach { file ->
                    if (file.name.endsWith(".json")) {
                        val itemView = LayoutInflater.from(this@MyAutoClickService)
                            .inflate(R.layout.item_script, null)
                        val tvName = itemView.findViewById<TextView>(R.id.tvScriptName)
                        val btnExport = itemView.findViewById<Button>(R.id.btnExportScriptFile)
                        val btnCopy = itemView.findViewById<Button>(R.id.btnCopyScriptFile)
                        val btnDelete = itemView.findViewById<Button>(R.id.btnDeleteScriptFile)

                        tvName?.text = file.nameWithoutExtension
                        tvName?.setOnClickListener {
                            loadScriptByName(file.nameWithoutExtension)
                            safeRemoveView(dialogView)
                        }

                        btnExport?.setOnClickListener {
                            exportScriptWithTemplates(
                                this@MyAutoClickService,
                                file.nameWithoutExtension
                            )
                        }

                        btnCopy?.setOnClickListener {
                            try {
                                val newName = "${file.nameWithoutExtension}_copy"
                                val newFile = File(dir, "$newName.json")
                                file.copyTo(newFile, overwrite = true)
                                refreshScriptsList()
                                Toast.makeText(this@MyAutoClickService, "📋 Скопировано: $newName", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) {
                                logError(this@MyAutoClickService, e)
                            }
                        }

                        btnDelete?.setOnClickListener {
                            file.delete()
                            refreshScriptsList()
                        }
                        layoutScriptsList?.addView(itemView)
                    }
                }
            }
        }

        refreshScriptsList()

        val etLoopCount = dialogView.findViewById<EditText>(R.id.etScriptLoopCount)
        val btnInfinite = dialogView.findViewById<Button>(R.id.btnToggleScriptInfinite)
        val btnRelay = dialogView.findViewById<Button>(R.id.btnSelectScriptRelay)

        etLoopCount?.setText(globalScriptLoopCount.toString())

        fun updateScriptHeaderUI() {
            btnInfinite?.text =
                if (isGlobalScriptInfinite) "Бесконечный цикл всего сценария: [ ВКЛ ]" else "Бесконечный цикл всего сценария: [ НЕТ ]"
            btnInfinite?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (isGlobalScriptInfinite) R.color.accent_blue else R.color.bg_dark_blue))

            btnRelay?.text =
                if (globalRelayNextScript.isNotEmpty()) "🔗 Эстафета: [ $globalRelayNextScript 📁 ]" else "🔗 Эстафета: [ Выбрать следующий сценарий 📁 ]"
            btnRelay?.backgroundTintList =
                ColorStateList.valueOf(getColor(if (globalRelayNextScript.isNotEmpty()) R.color.accent_blue else R.color.bg_dark_blue))
        }
        updateScriptHeaderUI()

        btnInfinite?.setOnClickListener {
            vibrateFeedback(20L)
            isGlobalScriptInfinite = !isGlobalScriptInfinite
            updateScriptHeaderUI()
        }

        btnRelay?.setOnClickListener {
            vibrateFeedback(20L)
            showScriptPickerDialog("Выберите следующий сценарий для эстафеты") { scName ->
                globalRelayNextScript = scName
                updateScriptHeaderUI()
            }
        }

        btnSaveScriptAction?.setOnClickListener {
            val name = etScriptName?.text?.toString()?.trim() ?: ""
            if (name.isNotEmpty()) {
                globalScriptLoopCount =
                    etLoopCount?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
                saveScriptByName(name)
                refreshScriptsList()
                etScriptName?.setText("")
            }
        }

        btnCloseScripts?.setOnClickListener { safeRemoveView(dialogView) }
        safeAddView(dialogView, params)
    }

    private fun showAddActionMenu() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.CENTER }

        val btnClick = dialogView.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = dialogView.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = dialogView.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelAdd)

        val spawnOffset = (actionsList.size % 8) * dpToPx(24).toFloat()
        val spawnX = 350f + spawnOffset
        val spawnY = 350f + spawnOffset

        btnClick?.setOnClickListener {
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1)
            safeRemoveView(dialogView)
        }
        btnSwipe?.setOnClickListener {
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1)
            spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f)
            safeRemoveView(dialogView)
        }
        btnAi?.setOnClickListener {
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0)
            safeRemoveView(dialogView)
        }
        btnCancel?.setOnClickListener { safeRemoveView(dialogView) }
        safeAddView(dialogView, params)
    }

    fun addNewActionAtPosition(
        posX: Float,
        posY: Float,
        recordedDelay: Long,
        actionType: ActionType,
        templateIndex: Int
    ) {
        val actionId = actionsList.size + 1
        val startView = LayoutInflater.from(this).inflate(R.layout.floating_target, null)
        val tvNum = startView.findViewById<TextView>(R.id.tvTargetNumber)
        tvNum?.text = actionId.toString()

        val initialSizeDp = if (actionType == ActionType.TRIGGER) 50 else 36
        val sizePx = dpToPx(initialSizeDp)

        val touchFlags = if (isRecording || isPlaying) {
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        } else {
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        }

        val params = WindowManager.LayoutParams(
            sizePx,
            sizePx,
            getOverlayType(),
            touchFlags,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        val config = ActionConfig(
            id = actionId,
            startView = startView,
            type = actionType,
            delay = recordedDelay,
            selectedTemplateIndex = templateIndex
        )

        startView.setOnTouchListener(object : View.OnTouchListener {
            private var initialX = 0
            private var initialY = 0
            private var initialTouchX = 0f
            private var initialTouchY = 0f
            private var isMoving = false

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false

                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = params.x
                        initialY = params.y
                        initialTouchX = event.rawX
                        initialTouchY = event.rawY
                        isMoving = false
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        val dx = abs(event.rawX - initialTouchX)
                        val dy = abs(event.rawY - initialTouchY)
                        if (dx > 8 || dy > 8) {
                            isMoving = true
                            val displayMetrics = resources.displayMetrics
                            val startSize = if (startView.width > 0) startView.width else dpToPx(36)
                            params.x = (initialX + (event.rawX - initialTouchX).toInt()).coerceIn(
                                0,
                                displayMetrics.widthPixels - startSize
                            )
                            params.y = (initialY + (event.rawY - initialTouchY).toInt()).coerceIn(
                                0,
                                displayMetrics.heightPixels - startSize
                            )
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

        if (isRecording || isNumbersHidden) {
            startView.visibility = View.INVISIBLE
        }

        actionsList.add(config)
        safeAddView(startView, params)
    }

    private fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = dpToPx(36)
        val params = WindowManager.LayoutParams(
            sizePx, sizePx, getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        endView.setOnTouchListener(object : View.OnTouchListener {
            private var initialX = 0
            private var initialY = 0
            private var initialTouchX = 0f
            private var initialTouchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false

                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = params.x
                        initialY = params.y
                        initialTouchX = event.rawX
                        initialTouchY = event.rawY
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        val displayMetrics = resources.displayMetrics
                        val endSize = if (endView.width > 0) endView.width else dpToPx(36)
                        params.x = (initialX + (event.rawX - initialTouchX).toInt()).coerceIn(
                            0,
                            displayMetrics.widthPixels - endSize
                        )
                        params.y = (initialY + (event.rawY - initialTouchY).toInt()).coerceIn(
                            0,
                            displayMetrics.heightPixels - endSize
                        )
                        safeUpdateViewLayout(endView, params)
                        return true
                    }

                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        return true
                    }
                }
                return false
            }
        })

        if (isRecording || isNumbersHidden) {
            endView.visibility = View.INVISIBLE
        }

        config.endView = endView
        safeAddView(endView, params)
    }

    private fun isOverlayArea(x: Int, y: Int): Boolean {
        val overlays = listOf(
            joystickOverlayView,
            controlPanelView,
            recordBarView,
            floatingStopView
        )
        for (v in overlays) {
            if (v != null && v.visibility == View.VISIBLE) {
                val loc = IntArray(2)
                v.getLocationOnScreen(loc)
                val rect = Rect(loc[0], loc[1], loc[0] + v.width, loc[1] + v.height)
                if (rect.contains(x, y)) return true
            }
        }
        return false
    }

    fun startOverlayRecording() {
        isRecording = true
        isInjectingGesture = false
        lastRecordedTime = System.currentTimeMillis()
        logAppEvent(this, "RECORD_START", "🚀 Мгновенная запись касаний и свайпов")

        actionsList.forEach { act ->
            act.startView.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }

        controlPanelView?.visibility = View.GONE
        showFloatingStopButton()

        if (recordOverlayView == null) {
            recordOverlayView = View(this).apply {
                setBackgroundColor(0x01000000)
            }
        }

        val overlayParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        )

        var downX = 0f
        var downY = 0f
        var downTime = 0L

        recordOverlayView?.setOnTouchListener { v, event ->
            if (!isRecording || isInjectingGesture) return@setOnTouchListener false

            val x = event.rawX
            val y = event.rawY

            if (isOverlayArea(x.toInt(), y.toInt())) {
                return@setOnTouchListener false
            }

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = x
                    downY = y
                    downTime = System.currentTimeMillis()
                    logAppEvent(this, "RECORD_TOUCH_DOWN", "👇 Нажатие пальца: ($downX, $downY)")
                    return@setOnTouchListener true
                }

                MotionEvent.ACTION_MOVE -> {
                    return@setOnTouchListener true
                }

                MotionEvent.ACTION_UP -> {
                    v.performClick()
                    val upTime = System.currentTimeMillis()
                    val dist = hypot((x - downX).toDouble(), (y - downY).toDouble())
                    val delay = (downTime - lastRecordedTime).coerceIn(80L, 5000L)
                    val gestureHoldDuration = (upTime - downTime).coerceIn(80L, 3000L)
                    lastRecordedTime = downTime

                    logAppEvent(
                        this,
                        "RECORD_TOUCH_UP",
                        "👆 Отпускание пальца: dist=${dist.toInt()}px, hold=${gestureHoldDuration}ms, delay=${delay}ms"
                    )

                    isInjectingGesture = true
                    safeRemoveView(recordOverlayView)

                    Handler(Looper.getMainLooper()).postDelayed({
                        if (dist > 60) {
                            addNewActionAtPosition(downX, downY, delay, ActionType.SWIPE, -1)
                            val currentConfig = actionsList.last()
                            currentConfig.holdDuration = gestureHoldDuration
                            spawnEndTargetAtPosition(currentConfig, x, y)

                            performSwipeWithCallback(
                                downX,
                                downY,
                                x,
                                y,
                                duration = gestureHoldDuration
                            ) { success ->
                                Handler(Looper.getMainLooper()).postDelayed({
                                    safeAddView(recordOverlayView, overlayParams)
                                    isInjectingGesture = false
                                }, 30L)
                            }
                        } else {
                            addNewActionAtPosition(downX, downY, delay, ActionType.CLICK, -1)

                            performClickWithCallback(downX, downY, duration = 30L) { success ->
                                Handler(Looper.getMainLooper()).postDelayed({
                                    safeAddView(recordOverlayView, overlayParams)
                                    isInjectingGesture = false
                                }, 30L)
                            }
                        }
                    }, 25L)

                    return@setOnTouchListener true
                }
            }
            false
        }

        controlPanelView?.visibility = View.GONE
        safeAddView(recordOverlayView, overlayParams)
        showRecordBar()
    }

    fun stopOverlayRecording() {
        isRecording = false
        isInjectingGesture = false
        logAppEvent(this, "RECORD_STOP", "Остановка записи. Всего шагов: ${actionsList.size}")

        if (recordOverlayView != null) {
            safeRemoveView(recordOverlayView)
            recordOverlayView = null
        }

        if (recordBarView != null) {
            safeRemoveView(recordBarView)
            recordBarView = null
        }

        hideFloatingStopButton()
        controlPanelView?.visibility = View.VISIBLE

        actionsList.forEach { act ->
            act.startView.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    private fun showRecordBar() {
        if (recordBarView != null) return

        val btnStop = Button(this).apply {
            text = "⏹ СТОП ЗАПИСИ"
            setTextColor(Color.WHITE)
            textSize = 13f
            setTypeface(null, Typeface.BOLD)
            backgroundTintList = ColorStateList.valueOf(getColor(R.color.red_close))
            setPadding(dpToPx(16), dpToPx(8), dpToPx(16), dpToPx(8))
        }

        val barParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
            y = dpToPx(40)
        }

        btnStop.setOnClickListener {
            vibrateFeedback(30L)
            stopOverlayRecording()
            Toast.makeText(
                this,
                "Запись остановлена. Записано шагов: ${actionsList.size}",
                Toast.LENGTH_SHORT
            ).show()
        }

        recordBarView = btnStop
        safeAddView(recordBarView, barParams)
    }

    private fun showTutorialCard() {
        if (!isTutorialActive) return
        if (tutorialCardView != null) {
            tutorialCardView?.visibility = View.VISIBLE
            updateTutorialContent()
            return
        }

        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        tutorialCardView =
            LayoutInflater.from(contextThemeWrapper).inflate(R.layout.floating_tutorial_card, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        )

        val btnPrev = tutorialCardView!!.findViewById<Button>(R.id.btnTutPrev)
        val btnNext = tutorialCardView!!.findViewById<Button>(R.id.btnTutNext)
        val btnSkip = tutorialCardView!!.findViewById<Button>(R.id.btnTutSkip)

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

        safeAddView(tutorialCardView, params)
        updateTutorialContent()
    }

    private fun updateTutorialContent() {
        if (tutorialCardView == null) return

        val layoutSubMenu = controlPanelView?.findViewById<View>(R.id.layoutSubMenu)
        if (currentTutorialStep >= 5) {
            layoutSubMenu?.visibility = View.VISIBLE
        }

        val tvTitle = tutorialCardView!!.findViewById<TextView>(R.id.tvTutTitle)
        val tvDesc = tutorialCardView!!.findViewById<TextView>(R.id.tvTutDesc)
        val btnNext = tutorialCardView!!.findViewById<Button>(R.id.btnTutNext)

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

    private fun hideTutorial() {
        isTutorialActive = false
        if (tutorialCardView != null) {
            safeRemoveView(tutorialCardView)
            tutorialCardView = null
        }
    }

    private var executionThread: Thread? = null

    private fun startExecutionLoop() {
        if (executionThread != null) return
        executionThread = Thread {
            var currentIndex = 0
            uiExecutor.execute {
                controlPanelView?.visibility = View.GONE
                showFloatingStopButton()
            }
            while (isPlaying && actionsList.isNotEmpty()) {
                val action = actionsList[currentIndex]

                uiExecutor.execute {
                    actionsList.forEach { act ->
                        act.startView.scaleX = 1.0f
                        act.startView.scaleY = 1.0f
                        act.endView?.scaleX = 1.0f
                        act.endView?.scaleY = 1.0f
                    }
                    action.startView.animate().scaleX(1.35f).scaleY(1.35f).setDuration(150).start()
                    action.endView?.animate()?.scaleX(1.35f)?.scaleY(1.35f)?.setDuration(150)
                        ?.start()
                }

                try {
                    Thread.sleep(action.delay)
                } catch (e: InterruptedException) {
                    break
                }
                if (!isPlaying) break

                when (action.type) {
                    ActionType.CLICK -> {
                        var clickX = 0f
                        var clickY = 0f
                        val latch = CountDownLatch(1)
                        uiExecutor.execute {
                            val loc = IntArray(2)
                            action.startView.getLocationOnScreen(loc)
                            val size =
                                if (action.startView.width > 0) action.startView.width else dpToPx(36)
                            clickX = loc[0] + size / 2f + kotlin.random.Random.nextInt(
                                -action.randomRadius,
                                action.randomRadius + 1
                            )
                            clickY = loc[1] + size / 2f + kotlin.random.Random.nextInt(
                                -action.randomRadius,
                                action.randomRadius + 1
                            )
                            latch.countDown()
                        }
                        try {
                            latch.await()
                        } catch (_: Exception) {
                        }
                        showClickVisualizer(clickX, clickY)
                        performClick(clickX, clickY, globalClickDurationMs)
                    }

                    ActionType.SWIPE -> {
                        if (action.endView != null) {
                            var startX = 0f
                            var startY = 0f
                            var endX = 0f
                            var endY = 0f
                            val latch = CountDownLatch(1)
                            uiExecutor.execute {
                                val loc1 = IntArray(2)
                                action.startView.getLocationOnScreen(loc1)
                                val loc2 = IntArray(2)
                                action.endView!!.getLocationOnScreen(loc2)
                                val size =
                                    if (action.startView.width > 0) action.startView.width else dpToPx(36)
                                startX = loc1[0] + size / 2f; startY = loc1[1] + size / 2f
                                endX = loc2[0] + size / 2f; endY = loc2[1] + size / 2f
                                latch.countDown()
                            }
                            try {
                                latch.await()
                            } catch (_: Exception) {
                            }
                            performSwipe(startX, startY, endX, endY, action.holdDuration)
                        }
                    }

                    ActionType.TRIGGER -> {
                        val jumpTargetStepId = executeAiTriggerSequence(action)
                        if (jumpTargetStepId == -999) {
                            currentIndex = 0
                            continue
                        } else if (jumpTargetStepId > 0) {
                            val targetIdx = actionsList.indexOfFirst { it.id == jumpTargetStepId }
                            if (targetIdx != -1) {
                                currentIndex = targetIdx
                                continue
                            }
                        }
                    }

                    else -> {}
                }

                val nextIdx = (currentIndex + 1) % actionsList.size
                if (nextIdx == 0) {
                    if (!isGlobalScriptInfinite) {
                        globalScriptLoopCount--
                        if (globalScriptLoopCount <= 0) {
                            if (globalRelayNextScript.isNotEmpty()) {
                                val relaySc = globalRelayNextScript
                                uiExecutor.execute { loadScriptByName(relaySc) }
                                globalScriptLoopCount = 1
                                currentIndex = 0
                                try {
                                    Thread.sleep(800L)
                                } catch (_: Exception) {
                                }
                                continue
                            } else {
                                break
                            }
                        }
                    }
                }
                currentIndex = nextIdx
            }
            isPlaying = false
            uiExecutor.execute {
                hideFloatingStopButton()
                controlPanelView?.visibility = View.VISIBLE
                actionsList.forEach { act ->
                    act.startView.scaleX = 1.0f
                    act.startView.scaleY = 1.0f
                    act.endView?.scaleX = 1.0f
                    act.endView?.scaleY = 1.0f
                }
                val playBtn = controlPanelView?.findViewById<ImageButton>(R.id.btnPlay)
                playBtn?.setImageResource(R.drawable.ic_play)
                setTargetsTouchable(true)
            }
        }
        executionThread?.start()
    }

    private fun maskOverlayOnBitmap(bitmap: Bitmap, overlayView: View?) {
        val canvas = android.graphics.Canvas(bitmap)
        val paint = android.graphics.Paint().apply {
            color = Color.TRANSPARENT
            xfermode = android.graphics.PorterDuffXfermode(android.graphics.PorterDuff.Mode.CLEAR)
        }
        val overlays = mutableListOf<View?>()
        overlays.add(overlayView)
        overlays.add(controlPanelView)
        overlays.add(joystickOverlayView)
        overlays.add(floatingStopView)
        overlays.add(recordBarView)
        for (act in actionsList) {
            overlays.add(act.startView)
            overlays.add(act.endView)
        }
        for (v in overlays) {
            if (v != null && v.visibility == View.VISIBLE) {
                val loc = IntArray(2)
                v.getLocationOnScreen(loc)
                val rect = Rect(loc[0], loc[1], loc[0] + v.width, loc[1] + v.height)
                if (rect.left < bitmap.width && rect.top < bitmap.height) {
                    canvas.drawRect(rect, paint)
                }
            }
        }
    }

    private fun showFloatingStopButton() {
        if (floatingStopView != null) {
            floatingStopView?.visibility = View.VISIBLE
            return
        }

        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        floatingStopView =
            LayoutInflater.from(contextThemeWrapper).inflate(R.layout.floating_stop_button, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 100
            y = 200
        }

        val handleDrag = floatingStopView!!.findViewById<View>(R.id.handleDragStop)
        val btnStop = floatingStopView!!.findViewById<View>(R.id.btnFloatingStop)

        val dragListener = object : View.OnTouchListener {
            private var initX = 0
            private var initY = 0
            private var touchX = 0f
            private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = params.x; initY = params.y
                        touchX = event.rawX; touchY = event.rawY
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        val displayMetrics = resources.displayMetrics
                        params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(
                            0,
                            displayMetrics.widthPixels - dpToPx(80)
                        )
                        params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(
                            0,
                            displayMetrics.heightPixels - dpToPx(40)
                        )
                        safeUpdateViewLayout(floatingStopView, params)
                        return true
                    }
                }
                return false
            }
        }

        handleDrag?.setOnTouchListener(dragListener)

        btnStop?.setOnClickListener {
            vibrateFeedback(30L)
            isPlaying = false
            stopExecutionLoop()
            Toast.makeText(this, "⏹ Выполнение остановлено", Toast.LENGTH_SHORT).show()
        }

        safeAddView(floatingStopView, params)
    }

    private fun hideFloatingStopButton() {
        if (floatingStopView != null) {
            safeRemoveView(floatingStopView)
            floatingStopView = null
        }
    }

    private fun stopExecutionLoop() {
        isPlaying = false
        executionThread?.interrupt()
        executionThread = null
        uiExecutor.execute {
            hideFloatingStopButton()
            controlPanelView?.visibility = View.VISIBLE
            val playBtn = controlPanelView?.findViewById<ImageButton>(R.id.btnPlay)
            playBtn?.setImageResource(R.drawable.ic_play)
            setTargetsTouchable(true)
        }
    }

    private fun showCaptureFrame() {
        if (captureFrameView != null) {
            safeRemoveView(captureFrameView)
            captureFrameView = null
        }
        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        captureFrameView =
            LayoutInflater.from(contextThemeWrapper).inflate(R.layout.floating_capture_frame, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        captureFrameView?.setOnTouchListener { _, _ -> false }

        val layoutTopBar = captureFrameView!!.findViewById<View>(R.id.layoutTopBar)
        val layoutBottomBar = captureFrameView!!.findViewById<View>(R.id.layoutBottomBar)
        val captureSquare = captureFrameView!!.findViewById<View>(R.id.captureSquare)
        val handleMove = captureFrameView!!.findViewById<View>(R.id.handleMoveFrame)
        val handleResize = captureFrameView!!.findViewById<View>(R.id.handleResize)
        val btnCancel = captureFrameView!!.findViewById<ImageButton>(R.id.btnCancelCapture)
        val btnCapture = captureFrameView!!.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnToggleShape = captureFrameView!!.findViewById<Button>(R.id.btnToggleCaptureShape)
        val btnCaptureSearchArea =
            captureFrameView!!.findViewById<Button>(R.id.btnCaptureSearchArea)

        btnCaptureSearchArea?.setOnClickListener {
            vibrateFeedback(20L)
            Toast.makeText(
                this,
                "📐 Задайте желтую рамку Зоны Поиска в редактировании шага",
                Toast.LENGTH_SHORT
            ).show()
        }

        val displayMetrics = resources.displayMetrics
        val screenW = displayMetrics.widthPixels
        val screenH = displayMetrics.heightPixels

        val minSizePx = dpToPx(12)

        var frameW = dpToPx(100)
        var frameH = dpToPx(100)
        var frameX = (screenW - frameW) / 2
        var frameY = (screenH - frameH) / 2

        fun updateFramePositions() {
            frameW = frameW.coerceIn(minSizePx, screenW)
            frameH = frameH.coerceIn(minSizePx, screenH)
            frameX = frameX.coerceIn(0, screenW - frameW)
            frameY = frameY.coerceIn(0, screenH - frameH)

            captureSquare?.apply {
                layoutParams?.width = frameW
                layoutParams?.height = frameH
                translationX = frameX.toFloat()
                translationY = frameY.toFloat()
                requestLayout()
            }

            val topBarW = layoutTopBar?.width?.takeIf { it > 0 } ?: dpToPx(120)
            val topBarH = layoutTopBar?.height?.takeIf { it > 0 } ?: dpToPx(36)
            val botBarH = layoutBottomBar?.height?.takeIf { it > 0 } ?: dpToPx(36)

            val topBarX =
                (frameX + (frameW - topBarW) / 2).coerceIn(dpToPx(4), screenW - topBarW - dpToPx(4))

            val topBarY: Int
            val botBarY: Int

            if (frameY >= topBarH + dpToPx(8)) {
                topBarY = frameY - topBarH - dpToPx(4)
                botBarY = if (frameY + frameH + botBarH + dpToPx(8) <= screenH) {
                    frameY + frameH + dpToPx(4)
                } else {
                    frameY + frameH - botBarH - dpToPx(4)
                }
            } else {
                topBarY = frameY + frameH + dpToPx(4)
                botBarY = topBarY + topBarH + dpToPx(4)
            }

            layoutTopBar?.apply {
                translationX = topBarX.toFloat()
                translationY = topBarY.toFloat()
            }

            val botBarW = layoutBottomBar?.width?.takeIf { it > 0 } ?: dpToPx(80)
            val botBarX =
                (frameX + (frameW - botBarW) / 2).coerceIn(dpToPx(4), screenW - botBarW - dpToPx(4))

            layoutBottomBar?.apply {
                translationX = botBarX.toFloat()
                translationY = botBarY.toFloat()
            }
        }

        var isCircleShape = true
        btnToggleShape?.setOnClickListener {
            vibrateFeedback(20L)
            isCircleShape = !isCircleShape
            btnToggleShape.text = if (isCircleShape) "🔘" else "🔲"
            captureSquare?.setBackgroundResource(if (isCircleShape) R.drawable.border_capture else R.drawable.border_capture_square)
        }

        val dragListener = object : View.OnTouchListener {
            private var initFrameX = 0
            private var initFrameY = 0
            private var touchX = 0f
            private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initFrameX = frameX
                        initFrameY = frameY
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        frameX = initFrameX + (event.rawX - touchX).toInt()
                        frameY = initFrameY + (event.rawY - touchY).toInt()
                        updateFramePositions()
                        return true
                    }
                }
                return false
            }
        }

        handleMove?.setOnTouchListener(dragListener)
        captureSquare?.setOnTouchListener(dragListener)

        handleResize?.setOnTouchListener(object : View.OnTouchListener {
            private var initW = 0
            private var initH = 0
            private var touchX = 0f
            private var touchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initW = frameW
                        initH = frameH
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        frameW = initW + (event.rawX - touchX).toInt()
                        frameH = initH + (event.rawY - touchY).toInt()
                        updateFramePositions()
                        return true
                    }
                }
                return false
            }
        })

        btnCancel?.setOnClickListener {
            vibrateFeedback(25L)
            safeRemoveView(captureFrameView)
            captureFrameView = null
        }

        btnCapture?.setOnClickListener {
            vibrateFeedback(50L)
            val cropX = frameX.coerceAtLeast(0)
            val cropY = frameY.coerceAtLeast(0)
            val cropW = frameW
            val cropH = frameH

            safeRemoveView(captureFrameView)
            captureFrameView = null

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                uiExecutor.execute {
                    controlPanelView?.visibility = View.INVISIBLE
                    Toast.makeText(
                        this@MyAutoClickService,
                        "🔍 ИИ сканирует экран...",
                        Toast.LENGTH_SHORT
                    ).show()
                }
                Handler(Looper.getMainLooper()).postDelayed({
                    takeScreenshot(
                        Display.DEFAULT_DISPLAY,
                        bgScannerExecutor,
                        object : TakeScreenshotCallback {
                            override fun onSuccess(screenshotResult: ScreenshotResult) {
                                val hwBuffer = screenshotResult.hardwareBuffer
                                try {
                                    val hwBitmap = Bitmap.wrapHardwareBuffer(
                                        hwBuffer,
                                        screenshotResult.colorSpace
                                    )
                                    val softwareBitmap =
                                        hwBitmap?.copy(Bitmap.Config.ARGB_8888, false)
                                    if (softwareBitmap != null) {
                                        val realMetrics = android.util.DisplayMetrics()
                                        windowManager.defaultDisplay.getRealMetrics(realMetrics)
                                        val scaleX =
                                            softwareBitmap.width.toFloat() / realMetrics.widthPixels.toFloat()
                                        val scaleY =
                                            softwareBitmap.height.toFloat() / realMetrics.heightPixels.toFloat()

                                        val realCropX = (cropX * scaleX).toInt()
                                            .coerceIn(0, softwareBitmap.width - 1)
                                        val realCropY = (cropY * scaleY).toInt()
                                            .coerceIn(0, softwareBitmap.height - 1)
                                        val realCropW = (cropW * scaleX).toInt().coerceIn(
                                            10,
                                            (softwareBitmap.width - realCropX).coerceAtLeast(10)
                                        )
                                        val realCropH = (cropH * scaleY).toInt().coerceIn(
                                            10,
                                            (softwareBitmap.height - realCropY).coerceAtLeast(10)
                                        )

                                        val cropped = Bitmap.createBitmap(
                                            softwareBitmap,
                                            realCropX,
                                            realCropY,
                                            realCropW,
                                            realCropH
                                        )
                                        val smartMask = generateSmartMask(cropped, isCircleShape)

                                        val ts = System.currentTimeMillis()
                                        val tDir =
                                            File(filesDir, "templates/default").apply { mkdirs() }
                                        val maskFile = File(tDir, "mask_$ts.png")
                                        val fullFile = File(tDir, "full_$ts.png")

                                        FileOutputStream(maskFile).use { out ->
                                            smartMask.compress(
                                                Bitmap.CompressFormat.PNG,
                                                100,
                                                out
                                            )
                                        }
                                        FileOutputStream(fullFile).use { out ->
                                            softwareBitmap.compress(
                                                Bitmap.CompressFormat.PNG,
                                                100,
                                                out
                                            )
                                        }

                                        val metaFile =
                                            getTemplateMetadataFile(maskFile.absolutePath)
                                        val meta = analyzeTemplate(cropped)
                                        meta.put("similarityPercent", 80)
                                        meta.put("originX", realCropX)
                                        meta.put("originY", realCropY)
                                        meta.put("originW", realCropW)
                                        meta.put("originH", realCropH)
                                        meta.put("isCircleShape", isCircleShape)
                                        FileOutputStream(metaFile).use { out ->
                                            out.write(
                                                meta.toString().toByteArray()
                                            )
                                        }

                                        logAppEvent(
                                            this@MyAutoClickService,
                                            "Capture",
                                            "Шаблон сохранён сразу при захвате: ${maskFile.absolutePath}"
                                        )

                                        uiExecutor.execute {
                                            loadAllTemplatesFromDisk()
                                            val newIndex =
                                                globalTemplatesNames.indexOf(maskFile.absolutePath)
                                            val spawnOffset =
                                                (actionsList.size % 8) * dpToPx(24).toFloat()
                                            addNewActionAtPosition(
                                                350f + spawnOffset,
                                                350f + spawnOffset,
                                                1000L,
                                                ActionType.TRIGGER,
                                                newIndex
                                            )
                                            Toast.makeText(
                                                this@MyAutoClickService,
                                                "🎉 ИИ-Шаблон успешно создан и сохранен!",
                                                Toast.LENGTH_SHORT
                                            ).show()

                                            val createdConfig = actionsList.last()
                                            startTemplateCalibration(createdConfig)
                                        }
                                    }
                                } catch (e: Exception) {
                                    logError(this@MyAutoClickService, e)
                                    uiExecutor.execute {
                                        controlPanelView?.visibility = View.VISIBLE
                                    }
                                } finally {
                                    hwBuffer.close()
                                }
                            }

                            override fun onFailure(errorCode: Int) {
                                uiExecutor.execute { controlPanelView?.visibility = View.VISIBLE }
                            }
                        })
                }, 300L)
            }
        }

        safeAddView(captureFrameView, params)
        captureFrameView?.post {
            updateFramePositions()
        }
    }

    private fun analyzeTemplate(template: Bitmap): JSONObject {
        return TemplateMatcher.analyzeTemplate(template)
    }

    fun findTemplateMatchForIndex(
        screenBitmap: Bitmap?,
        action: ActionConfig,
        templateIdx: Int
    ): MatchCandidate? {
        if (screenBitmap == null) return null
        if (templateIdx !in globalTemplates.indices) return null
        val templatePath = globalTemplatesNames[templateIdx]
        val template = globalTemplates[templateIdx]
        val meta = loadTemplateMetadata(templatePath)

        val savedPct = meta?.optInt("similarityPercent", 70) ?: 70
        val targetThreshold = (savedPct / 100f).coerceIn(0.10f, 0.99f)
        val localRangeThreshold = (targetThreshold - 0.08f).coerceAtLeast(0.10f)
        val globalMinThreshold = (minOf(action.similarityPercent, savedPct) / 100f).coerceIn(0.10f, 0.99f)

        val candidates =
            TemplateMatcher.findTemplateCandidatesCoarseFine(screenBitmap, template, meta, action)
        if (candidates.isEmpty()) return null

        val best = candidates.first()

        if (best.score >= targetThreshold) return best
        if (best.score >= localRangeThreshold) return best
        if (best.score >= globalMinThreshold) return best

        return null
    }

    private fun showCandidatesSelectionOverlay(
        screenshot: Bitmap,
        smartMask: Bitmap,
        candidates: List<MatchCandidate>,
        isCircle: Boolean,
        existingConfig: ActionConfig?,
        existingTemplatePath: String?
    ) {
        removeCandidateSelectionOverlay()

        val realMetrics = android.util.DisplayMetrics()
        windowManager.defaultDisplay.getRealMetrics(realMetrics)
        val scaleX = screenshot.width.toFloat() / realMetrics.widthPixels.toFloat()
        val scaleY = screenshot.height.toFloat() / realMetrics.heightPixels.toFloat()

        val overlayView = FrameLayout(this).apply {
            setBackgroundColor(Color.parseColor("#40000000"))
            clipChildren = false
            clipToPadding = false
        }
        candidateSelectionOverlayView = overlayView

        val topBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setBackgroundColor(Color.parseColor("#F00D1117"))
            setPadding(dpToPx(12), dpToPx(48), dpToPx(12), dpToPx(10))

            val tvTitle = TextView(this@MyAutoClickService).apply {
                text =
                    if (existingConfig == null) "Выберите лучший вариант маски" else "Выберите вариант калибровки"
                setTextColor(Color.WHITE)
                textSize = 14f
                setTypeface(null, Typeface.BOLD)
                layoutParams =
                    LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f)
            }
            addView(tvTitle)

            val btnClose = Button(this@MyAutoClickService).apply {
                text = "✕"
                setTextColor(Color.WHITE)
                textSize = 14f
                setTypeface(null, Typeface.BOLD)
                backgroundTintList = ColorStateList.valueOf(Color.parseColor("#F04438"))
                layoutParams = LinearLayout.LayoutParams(dpToPx(32), dpToPx(32))
                insetTop = 0; insetBottom = 0; setPadding(0, 0, 0, 0)
                setOnClickListener {
                    vibrateFeedback(25L)
                    removeCandidateSelectionOverlay()
                    controlPanelView?.visibility = View.VISIBLE
                    if (existingConfig != null) showEditDialog(existingConfig)
                    screenshot.recycle()
                    if (existingConfig == null) smartMask.recycle()
                }
            }
            addView(btnClose)
        }

        val topBarParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        ).apply {
            gravity = Gravity.TOP
        }
        overlayView.addView(topBar, topBarParams)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        for (cand in candidates) {
            val screenW = (cand.rect.width() / scaleX).toInt().coerceAtLeast(dpToPx(36))
            val screenH = (cand.rect.height() / scaleY).toInt().coerceAtLeast(dpToPx(36))

            val maxLeft = (realMetrics.widthPixels - screenW - dpToPx(8)).coerceAtLeast(dpToPx(4))
            val maxTop = (realMetrics.heightPixels - screenH - dpToPx(40)).coerceAtLeast(dpToPx(60))

            val screenLeft = (cand.rect.left / scaleX).toInt().coerceIn(dpToPx(4), maxLeft)
            val screenTop = (cand.rect.top / scaleY).toInt().coerceIn(dpToPx(60), maxTop)

            val pctInt = (cand.score * 100).toInt().coerceIn(1, 99)
            val strokeColor = when {
                pctInt >= 85 -> Color.parseColor("#34C759")
                pctInt >= 70 -> Color.parseColor("#FFB703")
                else -> Color.parseColor("#FF3B30")
            }

            val candBox = FrameLayout(this).apply {
                clipChildren = false
                clipToPadding = false

                val borderView = View(this@MyAutoClickService).apply {
                    val gd = android.graphics.drawable.GradientDrawable().apply {
                        setStroke(dpToPx(3.5f), strokeColor)
                        setColor(Color.TRANSPARENT)
                        cornerRadius = dpToPx(6).toFloat()
                    }
                    background = gd
                    layoutParams = FrameLayout.LayoutParams(screenW, screenH)
                }
                addView(borderView)

                val tvScore = TextView(this@MyAutoClickService).apply {
                    text = "$pctInt%"
                    setTextColor(strokeColor)
                    textSize = 11f
                    setTypeface(null, Typeface.BOLD)
                    gravity = Gravity.CENTER
                    setShadowLayer(3f, 1f, 1f, Color.BLACK)
                    background = null
                    setPadding(dpToPx(2), 0, dpToPx(2), 0)
                }

                val scoreTopMargin = if (screenTop < dpToPx(80)) dpToPx(2) else -dpToPx(18)
                val scoreParams = FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                    topMargin = scoreTopMargin
                }
                addView(tvScore, scoreParams)

                setOnClickListener {
                    vibrateFeedback(30L)
                    removeCandidateSelectionOverlay()

                    bgScannerExecutor.execute {
                        try {
                            val cropW = cand.rect.width()
                            val cropH = cand.rect.height()
                            val safeX = cand.rect.left.coerceAtLeast(0)
                            val safeY = cand.rect.top.coerceAtLeast(0)
                            val safeW = cropW.coerceAtMost(screenshot.width - safeX)
                            val safeH = cropH.coerceAtMost(screenshot.height - safeY)

                            val cropped =
                                Bitmap.createBitmap(screenshot, safeX, safeY, safeW, safeH)
                            val finalSmartMask =
                                TemplateMatcher.generateSmartMask(cropped, isCircle)

                            val ts = System.currentTimeMillis()
                            val tPath = existingTemplatePath ?: File(
                                File(
                                    filesDir,
                                    "templates/default"
                                ).apply { mkdirs() }, "mask_$ts.png"
                            ).absolutePath
                            val fPath = existingTemplatePath?.replace("mask_", "full_") ?: File(
                                File(
                                    filesDir,
                                    "templates/default"
                                ).apply { mkdirs() }, "full_$ts.png"
                            ).absolutePath

                            FileOutputStream(File(tPath)).use { out ->
                                finalSmartMask.compress(
                                    Bitmap.CompressFormat.PNG,
                                    100,
                                    out
                                )
                            }
                            if (existingConfig == null) {
                                FileOutputStream(File(fPath)).use { out ->
                                    screenshot.compress(
                                        Bitmap.CompressFormat.PNG,
                                        100,
                                        out
                                    )
                                }
                            }

                            val metaFile = getTemplateMetadataFile(tPath)
                            val meta = TemplateMatcher.analyzeTemplate(cropped)
                            meta.put("similarityPercent", pctInt)
                            meta.put("originX", safeX)
                            meta.put("originY", safeY)
                            meta.put("originW", safeW)
                            meta.put("originH", safeH)
                            meta.put("isCircleShape", isCircle)
                            FileOutputStream(metaFile).use { out ->
                                out.write(
                                    meta.toString().toByteArray()
                                )
                            }

                            uiExecutor.execute {
                                loadAllTemplatesFromDisk()
                                if (existingConfig != null) {
                                    existingConfig.similarityPercent = pctInt
                                    Toast.makeText(
                                        this@MyAutoClickService,
                                        "✅ Шаблон калиброван ($pctInt%)!",
                                        Toast.LENGTH_SHORT
                                    ).show()
                                    showEditDialog(existingConfig)
                                }
                                controlPanelView?.visibility = View.VISIBLE
                            }
                            cropped.recycle()
                            finalSmartMask.recycle()
                            if (existingConfig == null) smartMask.recycle()
                            screenshot.recycle()
                        } catch (e: Exception) {
                            logError(this@MyAutoClickService, e)
                        }
                    }
                }
            }

            val candParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                leftMargin = screenLeft
                topMargin = screenTop
            }
            overlayView.addView(candBox, candParams)
        }

        safeAddView(overlayView, params)
    }

    private fun startTemplateCalibration(config: ActionConfig) {
        if (config.selectedTemplateIndex !in globalTemplates.indices) return
        isCalibrationCancelled = false

        val progressView =
            LayoutInflater.from(this).inflate(R.layout.floating_calibration_box, null)
        val tvProgress = progressView.findViewById<TextView>(R.id.tvCandidatePercent)
        tvProgress?.text = "Сканирование экрана..."

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        )
        safeAddView(progressView, params)
        controlPanelView?.visibility = View.INVISIBLE

        Handler(Looper.getMainLooper()).postDelayed({
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                takeScreenshot(
                    Display.DEFAULT_DISPLAY,
                    bgScannerExecutor,
                    object : TakeScreenshotCallback {
                        override fun onSuccess(screenshotResult: ScreenshotResult) {
                            val hwBuffer = screenshotResult.hardwareBuffer
                            try {
                                val hwBitmap =
                                    Bitmap.wrapHardwareBuffer(hwBuffer, screenshotResult.colorSpace)
                                val softwareBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                                if (softwareBitmap != null) {
                                    maskOverlayOnBitmap(
                                        softwareBitmap,
                                        floatingStopView ?: controlPanelView
                                    )
                                    bgScannerExecutor.execute {
                                        runSmartCalibration(
                                            softwareBitmap,
                                            config,
                                            tvProgress,
                                            progressView
                                        )
                                    }
                                }
                            } catch (e: Exception) {
                                uiExecutor.execute {
                                    safeRemoveView(progressView); controlPanelView?.visibility =
                                    View.VISIBLE
                                }
                            } finally {
                                hwBuffer.close()
                            }
                        }

                        override fun onFailure(errorCode: Int) {
                            uiExecutor.execute {
                                safeRemoveView(progressView); controlPanelView?.visibility =
                                View.VISIBLE
                            }
                        }
                    })
            }
        }, 300L)
    }

    private fun runSmartCalibration(
        bitmap: Bitmap,
        config: ActionConfig,
        tvProgress: TextView?,
        progressView: View?
    ) {
        val template = globalTemplates[config.selectedTemplateIndex]
        val templatePath = globalTemplatesNames[config.selectedTemplateIndex]
        val meta = loadTemplateMetadata(templatePath)
        val isCircle = meta?.optBoolean("isCircleShape", true) ?: true

        uiExecutor.execute { tvProgress?.text = "Поиск кандидатов..." }

        val candidates =
            TemplateMatcher.findTemplateCandidatesCoarseFine(bitmap, template, meta, config)

        uiExecutor.execute {
            safeRemoveView(progressView)
            if (isCalibrationCancelled) {
                controlPanelView?.visibility = View.VISIBLE
                showEditDialog(config)
                bitmap.recycle()
                return@execute
            }
            if (candidates.isEmpty()) {
                Toast.makeText(
                    this,
                    "Кандидаты не найдены! Сделайте новый снимок маски.",
                    Toast.LENGTH_LONG
                ).show()
                controlPanelView?.visibility = View.VISIBLE
                showEditDialog(config)
                bitmap.recycle()
                return@execute
            }
            showCandidatesSelectionOverlay(
                bitmap,
                template,
                candidates,
                isCircle,
                config,
                templatePath
            )
        }
    }

    private var highlightBoxView: View? = null

    private fun showHighlightBox(rect: Rect, score: Float = 0.85f) {
        uiExecutor.execute {
            if (highlightBoxView != null) {
                safeRemoveView(highlightBoxView)
                highlightBoxView = null
            }

            val strokeColor = when {
                score >= 0.85f -> Color.parseColor("#34C759")
                score >= 0.70f -> Color.parseColor("#FFB703")
                else -> Color.parseColor("#FF3B30")
            }

            highlightBoxView = View(this).apply {
                val gd = android.graphics.drawable.GradientDrawable()
                gd.setStroke(dpToPx(3.5f), strokeColor)
                gd.setColor(Color.TRANSPARENT)
                gd.cornerRadius = dpToPx(6).toFloat()
                background = gd
            }

            val params = WindowManager.LayoutParams(
                rect.width(),
                rect.height(),
                getOverlayType(),
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                x = rect.left
                y = rect.top
            }

            safeAddView(highlightBoxView, params)

            Handler(Looper.getMainLooper()).postDelayed({
                if (highlightBoxView != null) {
                    safeRemoveView(highlightBoxView)
                    highlightBoxView = null
                }
            }, 1500L)
        }
    }

    private fun generateSmartMask(src: Bitmap, isCircle: Boolean): Bitmap {
        return TemplateMatcher.generateSmartMask(src, isCircle)
    }

    private fun executeAiTriggerSequence(action: ActionConfig): Int {
        var triggeredJumpStep = -1
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R || !isPlaying) return -1

        val latchHint = CountDownLatch(1)
        uiExecutor.execute {
            showAiSearchHint(action.id)
            latchHint.countDown()
        }
        try { latchHint.await() } catch (_: Exception) {}

        val scanIntervalMs = 2000L
        val postMatchMs = if (action.postMatchDelaySeconds <= 0) 2000L else action.postMatchDelaySeconds * 1000L
        val templatesToSearch = if (action.multiTemplateIndices.isNotEmpty()) {
            action.multiTemplateIndices.filter { it in globalTemplates.indices }
        } else {
            if (action.selectedTemplateIndex in globalTemplates.indices) listOf(action.selectedTemplateIndex) else emptyList()
        }

        if (templatesToSearch.isEmpty()) {
            uiExecutor.execute { hideAiSearchHint() }
            return -1
        }

        val isStandaloneOrContinuous = (actionsList.size <= 1) || (action.repeatCount == -1) ||
                (actionsList.indexOf(action) == actionsList.lastIndex && isGlobalScriptInfinite && action.jumpToStepOnMatch <= 0 && action.targetScriptToLoad.isEmpty())

        while (isPlaying) {
            val loopStartTime = System.currentTimeMillis()
            var localMatchFound = false
            val screenshotLatch = CountDownLatch(1)

            takeScreenshot(
                Display.DEFAULT_DISPLAY,
                bgScannerExecutor,
                object : TakeScreenshotCallback {
                    override fun onSuccess(screenshotResult: ScreenshotResult) {
                        val hwBuffer = screenshotResult.hardwareBuffer
                        try {
                            if (!isPlaying) return

                            val hwBitmap = Bitmap.wrapHardwareBuffer(hwBuffer, screenshotResult.colorSpace)
                            val softwareBitmap = hwBitmap?.copy(Bitmap.Config.ARGB_8888, true)
                            if (softwareBitmap != null) {
                                maskOverlayOnBitmap(softwareBitmap, floatingStopView ?: controlPanelView)

                                var foundMatch: MatchCandidate? = null
                                var matchedTemplateIdx = -1

                                for (tIdx in templatesToSearch) {
                                    if (!isPlaying) break
                                    val match = findTemplateMatchForIndex(softwareBitmap, action, tIdx)
                                    if (match != null) {
                                        foundMatch = match
                                        matchedTemplateIdx = tIdx
                                        break
                                    }
                                }

                                if (foundMatch != null && isPlaying) {
                                    val match = foundMatch
                                    localMatchFound = true

                                    if (action.targetScriptToLoad.isNotEmpty()) {
                                        val scToLoad = action.targetScriptToLoad
                                        uiExecutor.execute { loadScriptByName(scToLoad) }
                                        triggeredJumpStep = -999
                                    } else if (action.jumpToStepOnMatch > 0) {
                                        triggeredJumpStep = action.jumpToStepOnMatch
                                    }

                                    if (action.playAudioOnMatch) {
                                        playMatchNotification()
                                    }

                                    val realMetrics = android.util.DisplayMetrics()
                                    windowManager.defaultDisplay.getRealMetrics(realMetrics)
                                    val scaleX = softwareBitmap.width.toFloat() / realMetrics.widthPixels.toFloat()
                                    val scaleY = softwareBitmap.height.toFloat() / realMetrics.heightPixels.toFloat()

                                    val clickX = match.point.x.toFloat() / scaleX
                                    val clickY = match.point.y.toFloat() / scaleY

                                    val screenRect = Rect(
                                        (match.rect.left / scaleX).toInt(),
                                        (match.rect.top / scaleY).toInt(),
                                        (match.rect.right / scaleX).toInt(),
                                        (match.rect.bottom / scaleY).toInt()
                                    )

                                    showHighlightBox(screenRect, match.score)
                                    showClickVisualizer(clickX, clickY)

                                    if (action.clickAiTarget && isPlaying) {
                                        performClick(clickX, clickY, globalClickDurationMs)
                                    }
                                }
                                softwareBitmap.recycle()
                            }
                        } catch (e: Exception) {
                            logError(this@MyAutoClickService, e)
                        } finally {
                            hwBuffer.close()
                            screenshotLatch.countDown()
                        }
                    }

                    override fun onFailure(errorCode: Int) {
                        screenshotLatch.countDown()
                    }
                }
            )

            try { screenshotLatch.await() } catch (_: Exception) {}

            if (!isPlaying) break

            if (localMatchFound) {
                if (triggeredJumpStep != -1 || !isPlaying) break
                try { Thread.sleep(postMatchMs) } catch (_: Exception) { break }
                if (!isStandaloneOrContinuous || !isPlaying) break
                continue
            }

            val elapsed = System.currentTimeMillis() - loopStartTime
            val remainingWait = scanIntervalMs - elapsed
            if (remainingWait > 0 && isPlaying) {
                try { Thread.sleep(remainingWait) } catch (_: Exception) { break }
            }
        }

        uiExecutor.execute { hideAiSearchHint() }
        return triggeredJumpStep
    }

    fun saveScriptByName(name: String) {
        try {
            val jsonArray = JSONArray()
            for (action in actionsList) {
                val obj = JSONObject().apply {
                    put("id", action.id)
                    put("type", action.type.name)
                    put("delay", action.delay)
                    put("repeatCount", action.repeatCount)
                    put("holdDuration", action.holdDuration)
                    put("randomRadius", action.randomRadius)

                    val templatePath =
                        if (action.selectedTemplateIndex in globalTemplatesNames.indices) {
                            globalTemplatesNames[action.selectedTemplateIndex]
                        } else ""
                    val templateFileName =
                        if (templatePath.isNotEmpty()) File(templatePath).name else ""

                    put("selectedTemplateIndex", action.selectedTemplateIndex)
                    put("templateFileName", templateFileName)
                    put("playAudioOnMatch", action.playAudioOnMatch)

                    val multiArr = JSONArray()
                    action.multiTemplateIndices.forEach { multiArr.put(it) }
                    put("multiTemplateIndices", multiArr)
                    put("clickAiTarget", action.clickAiTarget)
                    put("aiTimeoutSeconds", action.aiTimeoutSeconds)
                    put("similarityPercent", action.similarityPercent)
                    put("targetScriptToLoad", action.targetScriptToLoad)
                    put("jumpToStepOnMatch", action.jumpToStepOnMatch)
                    put("isFastMode", action.isFastMode)

                    val loc = IntArray(2)
                    action.startView.getLocationOnScreen(loc)
                    put("x", loc[0])
                    put("y", loc[1])
                    if (action.endView != null) {
                        val endLoc = IntArray(2)
                        action.endView!!.getLocationOnScreen(endLoc)
                        put("endX", endLoc[0])
                        put("endY", endLoc[1])
                    }
                }
                jsonArray.put(obj)
            }

            val dir = File(filesDir, "scripts")
            if (!dir.exists()) dir.mkdirs()
            val scriptFile = File(dir, "${name}.json")
            FileOutputStream(scriptFile).use { out ->
                out.write(jsonArray.toString().toByteArray())
            }
            Toast.makeText(this, "Сценарий '$name' сохранен!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun loadScriptByName(name: String) {
        try {
            val dir = File(filesDir, "scripts")
            val scriptFile = File(dir, "${name}.json")
            if (!scriptFile.exists()) return

            val jsonArray = JSONArray(scriptFile.readText())
            uiExecutor.execute {
                actionsList.forEach { act ->
                    safeRemoveView(act.startView)
                    act.endView?.let { safeRemoveView(it) }
                }
                actionsList.clear()

                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    val typeStr = obj.optString("type", "CLICK")
                    val type = try {
                        ActionType.valueOf(typeStr)
                    } catch (e: Exception) {
                        ActionType.CLICK
                    }

                    val x = obj.optInt("x", 500).toFloat()
                    val y = obj.optInt("y", 500).toFloat()
                    val delay = obj.optLong("delay", 1000L)

                    addNewActionAtPosition(x, y, delay, type, -1)

                    val newAction = actionsList.last()
                    newAction.holdDuration = obj.optLong("holdDuration", 1000L)
                    newAction.repeatCount = obj.optInt("repeatCount", 1)
                    newAction.randomRadius = obj.optInt("randomRadius", 0)

                    val tFileName = obj.optString("templateFileName", "")
                    val savedIdx = obj.optInt("selectedTemplateIndex", -1)

                    val matchedIdx = if (tFileName.isNotEmpty()) {
                        val foundIdx =
                            globalTemplatesNames.indexOfFirst { File(it).name == tFileName }
                        if (foundIdx != -1) foundIdx else savedIdx
                    } else savedIdx

                    newAction.selectedTemplateIndex = matchedIdx
                    newAction.clickAiTarget = obj.optBoolean("clickAiTarget", true)
                    newAction.playAudioOnMatch = obj.optBoolean("playAudioOnMatch", false)

                    if (obj.has("multiTemplateIndices")) {
                        val arr = obj.getJSONArray("multiTemplateIndices")
                        newAction.multiTemplateIndices.clear()
                        for (mIdx in 0 until arr.length()) {
                            newAction.multiTemplateIndices.add(arr.getInt(mIdx))
                        }
                    }
                    newAction.aiTimeoutSeconds = obj.optInt("aiTimeoutSeconds", 2)
                    newAction.similarityPercent = obj.optInt("similarityPercent", 80)
                    newAction.targetScriptToLoad = obj.optString("targetScriptToLoad", "")
                    newAction.jumpToStepOnMatch = obj.optInt("jumpToStepOnMatch", -1)
                    newAction.isFastMode = obj.optBoolean("isFastMode", true)

                    if (obj.has("endX") && obj.has("endY")) {
                        spawnEndTargetAtPosition(
                            newAction,
                            obj.getInt("endX").toFloat(),
                            obj.getInt("endY").toFloat()
                        )
                    }
                }
                Toast.makeText(
                    this,
                    "Сценарий '$name' успешно загружен! Шагов: ${actionsList.size}",
                    Toast.LENGTH_SHORT
                ).show()
            }
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    private fun purgeOldTrashTemplates() {
        try {
            val trashDir = File(filesDir, "trash_templates")
            if (trashDir.exists()) {
                val now = System.currentTimeMillis()
                val sevenDaysMs = 7L * 24 * 60 * 60 * 1000L
                trashDir.walkTopDown().forEach { file ->
                    if (file.isFile && (now - file.lastModified() > sevenDaysMs)) {
                        file.delete()
                    }
                }
            }
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    private fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || view.parent == null) return
        try {
            windowManager.updateViewLayout(view, params)
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    private fun safeRemoveView(view: View?) {
        if (view == null || view.parent == null) return
        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    private fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null) return
        try {
            windowManager.addView(view, params)
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    private fun dpToPx(dp: Int): Int {
        return (dp * resources.displayMetrics.density).toInt()
    }

    private fun dpToPx(dp: Float): Int {
        return (dp * resources.displayMetrics.density).toInt()
    }

    private fun getOverlayType(): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY
        } else {
            WindowManager.LayoutParams.TYPE_PHONE
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        loadAllTemplatesFromDisk()
    }

    override fun onUnbind(intent: Intent?): Boolean {
        instance = null
        return super.onUnbind(intent)
    }

    fun showControlPanel() {
        if (controlPanelView != null) {
            controlPanelView?.visibility = View.VISIBLE
            setTargetsTouchable(true)
            return
        }

        val contextThemeWrapper = ContextThemeWrapper(this, R.style.Theme_AutoTap)
        controlPanelView = LayoutInflater.from(contextThemeWrapper).inflate(R.layout.floating_control_panel, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 100
            y = 300
        }

        val handleDrag = controlPanelView!!.findViewById<View>(R.id.handleDrag)
        val layoutMainRow = controlPanelView!!.findViewById<View>(R.id.layoutMainRow)
        val layoutSubMenu = controlPanelView!!.findViewById<View>(R.id.layoutSubMenu)
        val btnSingleBubble = controlPanelView!!.findViewById<ImageButton>(R.id.btnSingleBubble)

        var panelCycleMode = 0

        fun applyPanelCycleState(mode: Int) {
            panelCycleMode = mode % 3
            when (panelCycleMode) {
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

            controlPanelView?.let { panel ->
                panel.requestLayout()
                panel.post {
                    val lp = panel.layoutParams as? WindowManager.LayoutParams ?: params
                    lp.width = WindowManager.LayoutParams.WRAP_CONTENT
                    lp.height = WindowManager.LayoutParams.WRAP_CONTENT
                    safeUpdateViewLayout(panel, lp)
                }
            }
        }

        val dragListener = object : View.OnTouchListener {
            private var initialX = 0
            private var initialY = 0
            private var initialTouchX = 0f
            private var initialTouchY = 0f

            override fun onTouch(v: View, event: MotionEvent): Boolean {
                if (isPlaying) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = params.x
                        initialY = params.y
                        initialTouchX = event.rawX
                        initialTouchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val displayMetrics = resources.displayMetrics
                        val maxX = displayMetrics.widthPixels - dpToPx(100)
                        val maxY = displayMetrics.heightPixels - dpToPx(50)

                        params.x = (initialX + (event.rawX - initialTouchX).toInt()).coerceIn(0, maxX)
                        params.y = (initialY + (event.rawY - initialTouchY).toInt()).coerceIn(0, maxY)
                        safeUpdateViewLayout(controlPanelView, params)
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        v.performClick()
                        return true
                    }
                }
                return false
            }
        }

        handleDrag?.setOnTouchListener(dragListener)

        btnSingleBubble?.setOnClickListener {
            vibrateFeedback(25L)
            applyPanelCycleState(0)
        }

        val btnPlay = controlPanelView!!.findViewById<ImageButton>(R.id.btnPlay)
        val btnAdd = controlPanelView!!.findViewById<ImageButton>(R.id.btnAdd)
        val btnClearAll = controlPanelView!!.findViewById<ImageButton>(R.id.btnClearAll)
        val btnToggleMenu = controlPanelView!!.findViewById<ImageButton>(R.id.btnToggleMenu)
        val btnRecord = controlPanelView!!.findViewById<ImageButton>(R.id.btnRecord)
        val btnLoadScript = controlPanelView!!.findViewById<ImageButton>(R.id.btnLoadScript)
        val btnClose = controlPanelView!!.findViewById<ImageButton>(R.id.btnClose)
        val btnHideNumbers = controlPanelView!!.findViewById<ImageButton>(R.id.btnHideNumbers)
        val btnToggleJoystick = controlPanelView!!.findViewById<ImageButton>(R.id.btnToggleJoystick)
        val btnCapturePool = controlPanelView!!.findViewById<ImageButton>(R.id.btnCapturePool)
        val btnHelpTutorial = controlPanelView!!.findViewById<ImageButton>(R.id.btnHelpTutorial)

        btnHideNumbers?.setOnClickListener {
            vibrateFeedback(25L)
            isNumbersHidden = !isNumbersHidden
            btnHideNumbers.setImageResource(if (isNumbersHidden) R.drawable.ic_eye_off else R.drawable.ic_eye)
            actionsList.forEach { act ->
                act.startView.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
                act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            }
        }

        btnToggleJoystick?.setOnClickListener {
            vibrateFeedback(25L)
            if (joystickOverlayView == null) {
                showJoystickManipulator()
                Toast.makeText(this, "🕹 Джойстик включен", Toast.LENGTH_SHORT).show()
            } else {
                safeRemoveView(joystickOverlayView)
                joystickOverlayView = null
            }
        }

        btnCapturePool?.setOnClickListener {
            vibrateFeedback(25L)
            showCaptureFrame()
        }

        btnHelpTutorial?.setOnClickListener {
            vibrateFeedback(25L)
            isTutorialActive = true
            currentTutorialStep = 0
            showTutorialCard()
        }

        btnPlay?.setOnClickListener {
            vibrateFeedback(30L)
            isPlaying = !isPlaying
            setTargetsTouchable(!isPlaying)
            btnPlay.setImageResource(if (isPlaying) R.drawable.ic_pause else R.drawable.ic_play)
            Toast.makeText(this, if (isPlaying) "▶ Запущено" else "⏸ Пауза", Toast.LENGTH_SHORT).show()
            if (isPlaying) {
                startExecutionLoop()
            } else {
                stopExecutionLoop()
            }
        }

        btnAdd?.setOnClickListener {
            vibrateFeedback(25L)
            showAddActionMenu()
        }

        btnRecord?.setOnClickListener {
            vibrateFeedback(30L)
            if (isRecording) {
                stopOverlayRecording()
            } else {
                startOverlayRecording()
                Toast.makeText(this, "🔴 Запись включена! Нажимайте по экрану.", Toast.LENGTH_SHORT).show()
            }
        }

        btnLoadScript?.setOnClickListener {
            vibrateFeedback(25L)
            showScriptsDialog()
        }

        btnClearAll?.setOnClickListener {
            vibrateFeedback(30L)
            actionsList.forEach {
                safeRemoveView(it.startView)
                it.endView?.let { ev -> safeRemoveView(ev) }
            }
            actionsList.clear()
            Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
        }

        btnToggleMenu?.setOnClickListener {
            vibrateFeedback(25L)
            applyPanelCycleState(panelCycleMode + 1)
        }

        btnClose?.setOnClickListener {
            vibrateFeedback(30L)
            this@MyAutoClickService.hideControlPanel(false)
        }

        safeAddView(controlPanelView, params)
        if (isTutorialActive) showTutorialCard()
    }

    fun hideControlPanel(openMainApp: Boolean = false) {
        isPlaying = false
        stopOverlayRecording()
        actionsList.forEach { action ->
            safeRemoveView(action.startView)
            action.endView?.let { safeRemoveView(it) }
        }
        actionsList.clear()

        if (joystickOverlayView != null) {
            safeRemoveView(joystickOverlayView)
            joystickOverlayView = null
        }

        removeCandidateSelectionOverlay()
        controlPanelView?.let { safeRemoveView(it); controlPanelView = null }

        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) {
                logError(this, e)
            }
        }
    }

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel(false)
        removeHighlightOverlay()
        removeCandidateSelectionOverlay()
        if (visualizerOverlay != null) {
            safeRemoveView(visualizerOverlay)
            visualizerOverlay = null
        }
        if (searchHintView != null) {
            safeRemoveView(searchHintView)
            searchHintView = null
        }
        instance = null
        bgScannerExecutor.shutdown()
        super.onDestroy()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    fun performClick(x: Float, y: Float, duration: Long = globalClickDurationMs) {
        performClickWithCallback(x, y, duration, null)
    }

    fun performClickWithCallback(
        x: Float,
        y: Float,
        duration: Long = globalClickDurationMs,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        logAppEvent(
            this,
            "GESTURE_DISPATCH",
            "📤 Отправка системного тапа в ОС: ($x, $y), duration=${duration}ms"
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val path = Path().apply { moveTo(x, y) }
            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            var isDone = false
            fun finish(success: Boolean, reason: String) {
                if (!isDone) {
                    isDone = true
                    onComplete?.invoke(success)
                }
            }

            Handler(Looper.getMainLooper()).postDelayed(
                { finish(false, "Timeout 150ms") },
                duration + 150L
            )

            val res = dispatchGesture(gesture, object : GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    super.onCompleted(gestureDescription)
                    finish(true, "Completed")
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    super.onCancelled(gestureDescription)
                    finish(false, "Cancelled by OS")
                }
            }, null)

            if (!res) {
                finish(false, "dispatchGesture returned false")
            }
        } else {
            onComplete?.invoke(false)
        }
    }

    fun performSwipe(
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        duration: Long = globalSwipeDurationMs
    ) {
        performSwipeWithCallback(startX, startY, endX, endY, duration, null)
    }

    fun performSwipeWithCallback(
        startX: Float,
        startY: Float,
        endX: Float,
        endY: Float,
        duration: Long = globalSwipeDurationMs,
        onComplete: ((Boolean) -> Unit)? = null
    ) {
        logAppEvent(
            this,
            "GESTURE_DISPATCH",
            "📤 Отправка свайпа в ОС: ($startX, $startY) -> ($endX, $endY), duration=${duration}ms"
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val path = Path().apply {
                moveTo(startX, startY)
                lineTo(endX, endY)
            }
            val stroke = GestureDescription.StrokeDescription(path, 0, duration)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()

            var isDone = false
            fun finish(success: Boolean, reason: String) {
                if (!isDone) {
                    isDone = true
                    onComplete?.invoke(success)
                }
            }

            Handler(Looper.getMainLooper()).postDelayed(
                { finish(false, "Timeout 150ms") },
                duration + 150L
            )

            val res = dispatchGesture(gesture, object : GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    super.onCompleted(gestureDescription)
                    finish(true, "Completed")
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    super.onCancelled(gestureDescription)
                    finish(false, "Cancelled by OS")
                }
            }, null)

            if (!res) {
                finish(false, "dispatchGesture returned false")
            }
        } else {
            onComplete?.invoke(false)
        }
    }

    fun loadTemplateMetadata(maskPath: String): JSONObject? {
        try {
            if (maskPath.isEmpty()) return null
            val metaFile = getTemplateMetadataFile(maskPath)
            if (metaFile.exists()) {
                return JSONObject(metaFile.readText())
            }
        } catch (_: Exception) {}
        return null
    }

    fun loadAllTemplatesFromDisk() {
        try {
            purgeOldTrashTemplates()
            globalTemplates.forEach {
                try { it.recycle() } catch (_: Exception) {}
            }
            globalTemplates.clear()
            globalTemplatesNames.clear()

            val baseDir = File(filesDir, "templates")
            if (baseDir.exists()) {
                val allMasks = baseDir.walkTopDown()
                    .filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }
                    .sortedBy { it.lastModified() }
                    .toList()

                allMasks.forEach { file ->
                    BitmapFactory.decodeFile(file.absolutePath)?.let { bmp ->
                        globalTemplates.add(bmp)
                        globalTemplatesNames.add(file.absolutePath)
                    }
                }
            }
            logAppEvent(this, "Templates", "Загружено ИИ-шаблонов с диска: ${globalTemplates.size}")
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun moveTemplateToTrash(index: Int) {
        if (index !in globalTemplatesNames.indices) return
        try {
            val maskPath = globalTemplatesNames[index]
            val maskFile = File(maskPath)
            if (maskFile.exists()) {
                val dateFolder = maskFile.parentFile?.name ?: "default"
                val targetTrashDir = File(File(filesDir, "trash_templates"), dateFolder).apply { mkdirs() }
                maskFile.renameTo(File(targetTrashDir, maskFile.name))
            }
            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)
            Toast.makeText(this, "🗑 Шаблон перемещен в корзину", Toast.LENGTH_SHORT).show()
            logAppEvent(this, "Templates", "Перемещен в корзину шаблон #$index: $maskPath")
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun exportScriptWithTemplates(context: Context, scriptName: String) {
        try {
            val scriptsDir = File(context.filesDir, "scripts")
            val scriptFile = File(scriptsDir, "$scriptName.json")
            if (!scriptFile.exists()) return

            val zipFile = File(context.externalCacheDir ?: context.cacheDir, "$scriptName.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val jsonBytes = scriptFile.readBytes()
            val jsonEntry = ZipEntry("scripts/$scriptName.json")
            zos.putNextEntry(jsonEntry)
            zos.write(jsonBytes)
            zos.closeEntry()

            val jsonArray = runCatching { JSONArray(String(jsonBytes)) }.getOrNull() ?: JSONArray()
            val exportedTemplates = HashSet<String>()

            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.optJSONObject(i) ?: continue
                val tFileName = obj.optString("templateFileName", "")
                val idx = obj.optInt("selectedTemplateIndex", -1)

                val maskPath = if (tFileName.isNotEmpty()) {
                    globalTemplatesNames.firstOrNull { File(it).name == tFileName }
                        ?: if (idx in globalTemplatesNames.indices) globalTemplatesNames[idx] else null
                } else if (idx in globalTemplatesNames.indices) {
                    globalTemplatesNames[idx]
                } else null

                if (maskPath != null && !exportedTemplates.contains(maskPath)) {
                    exportedTemplates.add(maskPath)
                    val maskFile = File(maskPath)
                    if (maskFile.exists()) {
                        val dateFolder = maskFile.parentFile?.name ?: "default"

                        val maskEntry = ZipEntry("templates/$dateFolder/${maskFile.name}")
                        zos.putNextEntry(maskEntry)
                        zos.write(maskFile.readBytes())
                        zos.closeEntry()

                        val fullFile = File(maskFile.parentFile, maskFile.name.replace("mask_", "full_"))
                        if (fullFile.exists()) {
                            val fullEntry = ZipEntry("templates/$dateFolder/${fullFile.name}")
                            zos.putNextEntry(fullEntry)
                            zos.write(fullFile.readBytes())
                            zos.closeEntry()
                        }

                        val metaFile = getTemplateMetadataFile(maskPath)
                        if (metaFile.exists()) {
                            val metaEntry = ZipEntry("templates/$dateFolder/${metaFile.name}")
                            zos.putNextEntry(metaEntry)
                            zos.write(metaEntry)
                            zos.closeEntry()
                        }
                    }
                }
            }

            zos.close()

            val uri = try {
                FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", zipFile)
            } catch (e: Exception) {
                logError(context, e)
                null
            }

            if (uri == null) {
                Toast.makeText(context, "Ошибка получения доступа к ZIP-файлу!", Toast.LENGTH_SHORT).show()
                return
            }

            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(Intent.EXTRA_SUBJECT, scriptName)
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(shareIntent, "Экспортировать").apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            })
            logAppEvent(context, "Export", "Сценарий '$scriptName' успешно экспортирован с шаблонами")
        } catch (e: Exception) {
            logError(context, e)
        }
    }
}
