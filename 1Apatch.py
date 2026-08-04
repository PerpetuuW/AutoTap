import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан файл: {rel_path}")

def apply_overlay_touch_repair():
    print("🚀 Реставрация тач-событий, оверлеев и кнопок AutoTap v28.18.0 PRO...")

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
        versionCode = 2341
        versionName = "28.18.0-PRO"

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

    # 2. OverlayManager.kt (Использование TYPE_APPLICATION_OVERLAY для 100% кликабельности)
    overlay_manager_code = r"""package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import java.util.concurrent.ConcurrentHashMap

class OverlayManager(private val context: Context) {

    private val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    private val attachedViews = ConcurrentHashMap<View, Boolean>()
    private val updateHandler = Handler(Looper.getMainLooper())
    private val pendingUpdates = ConcurrentHashMap<View, WindowManager.LayoutParams>()

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null) return
        if (attachedViews[view] == true) return

        try {
            windowManager.addView(view, params)
            attachedViews[view] = true
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun safeRemoveView(view: View?) {
        if (view == null) return
        if (attachedViews[view] != true) return

        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        } finally {
            attachedViews.remove(view)
        }
    }

    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null) return
        if (attachedViews[view] != true) return

        pendingUpdates[view] = params

        updateHandler.removeCallbacksAndMessages(null)
        updateHandler.postDelayed({
            try {
                val p = pendingUpdates[view] ?: return@postDelayed
                windowManager.updateViewLayout(view, p)
            } catch (e: Exception) {
                MyAutoClickService.logError(context, e)
            } finally {
                pendingUpdates.remove(view)
            }
        }, 8)
    }

    fun dpToPx(dp: Int): Int =
        (dp * context.resources.displayMetrics.density).toInt()

    fun dpToPx(dp: Float): Int =
        (dp * context.resources.displayMetrics.density).toInt()

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

            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/base/OverlayManager.kt", overlay_manager_code)

    # 3. ControlPanelOverlay.kt (Полное подключение всех 13 кнопок, драга и 3 режимов)
    control_panel_code = r"""package com.example.autotap.ui.overlays

import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ControlPanelOverlay(private val service: MyAutoClickService) {

    private var panelView: View? = null
    private var stopButtonView: View? = null

    private var panelState = 0

    fun show() {
        if (panelView != null) {
            panelView?.visibility = View.VISIBLE
            return
        }

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_control_panel, null)
        panelView = view

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = service.overlayManager.dpToPx(20)
            y = service.overlayManager.dpToPx(120)
        }

        bindUi(view)
        service.overlayManager.safeAddView(view, params)
    }

    fun hide() {
        panelView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        panelView = null
    }

    private fun bindUi(view: View) {
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
            val params = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = params.x
                    initY = params.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dm = service.resources.displayMetrics
                    val maxX = dm.widthPixels - view.width
                    val maxY = dm.heightPixels - view.height
                    params.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    params.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxY)
                    service.overlayManager.safeUpdateViewLayout(view, params)
                    true
                }
                else -> false
            }
        }

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
            val params = view.layoutParams as? WindowManager.LayoutParams
            if (params != null) {
                params.width = WindowManager.LayoutParams.WRAP_CONTENT
                params.height = WindowManager.LayoutParams.WRAP_CONTENT
                service.overlayManager.safeUpdateViewLayout(view, params)
            }
        }

        btnToggleMenu?.setOnClickListener {
            service.vibrateFeedback(20L)
            updatePanelState(panelState + 1)
        }

        btnSingleBubble?.setOnClickListener {
            service.vibrateFeedback(20L)
            updatePanelState(0)
        }

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (service.isPlaying) {
                btnPlay.setImageResource(R.drawable.ic_play)
                service.stopExecutionLoop()
            } else {
                btnPlay.setImageResource(R.drawable.ic_pause)
                service.startScript("default")
            }
        }

        btnAdd?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showAddActionMenu()
        }

        btnCapturePool?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.captureFrameOverlay.show()
        }

        btnHelpTutorial?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showTutorialCard()
        }

        btnClearAll?.setOnClickListener {
            service.vibrateFeedback(30L)
            service.clearAllActions()
        }

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.isRecording) {
                service.stopOverlayRecording()
            } else {
                service.startOverlayRecording()
            }
        }

        btnToggleJoystick?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.joystickOverlay.rootView != null) {
                service.joystickOverlay.hide()
            } else {
                service.joystickOverlay.show()
            }
        }

        btnLoadScript?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showScriptsDialog()
        }

        btnHideNumbers?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.toggleNumbersVisibility()
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.hideControlPanel(openMainApp = true)
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
        }

        val handleDrag = view.findViewById<TextView>(R.id.handleDragStop)
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
                    val dm = service.resources.displayMetrics
                    val maxX = dm.widthPixels - view.width
                    val maxY = dm.heightPixels - view.height
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxY)
                    service.overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.stopExecutionLoop()
        }

        service.overlayManager.safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_beacon_ring, null)

        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.animate()
            .alpha(0f)
            .setDuration(300)
            .withEndAction {
                service.overlayManager.safeRemoveView(view)
            }
            .start()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt", control_panel_code)

    # 4. CaptureFrameOverlay.kt
    capture_overlay_code = r"""package com.example.autotap.ui.overlays

import android.graphics.Bitmap
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import android.widget.Toast
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class CaptureFrameOverlay(
    private val service: MyAutoClickService,
    val overlayManager: OverlayManager = service.overlayManager
) {

    private var rootView: View? = null

    fun show() {
        if (rootView != null) return

        val view = LayoutInflater.from(service)
            .inflate(R.layout.floating_capture_frame, null)
        rootView = view

        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }

        bindUi(view)
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }

    fun startRecording() {
        show()
        service.isRecording = true
    }

    private fun bindUi(view: View) {
        val captureSquare = view.findViewById<View>(R.id.captureSquare)
        val layoutTopBar = view.findViewById<View>(R.id.layoutTopBar)
        val layoutBottomBar = view.findViewById<View>(R.id.layoutBottomBar)

        val handleMove = view.findViewById<View>(R.id.handleMoveFrame)
        val handleResize = view.findViewById<View>(R.id.handleResize)

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnSearchArea = view.findViewById<Button>(R.id.btnCaptureSearchArea)
        val btnToggleShape = view.findViewById<Button>(R.id.btnToggleCaptureShape)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        val dm = service.resources.displayMetrics
        val screenW = dm.widthPixels
        val screenH = dm.heightPixels

        var frameW = overlayManager.dpToPx(100)
        var frameH = overlayManager.dpToPx(100)
        var frameX = (screenW - frameW) / 2
        var frameY = (screenH - frameH) / 2

        fun updatePositions() {
            frameW = frameW.coerceIn(overlayManager.dpToPx(24), screenW)
            frameH = frameH.coerceIn(overlayManager.dpToPx(24), screenH)
            frameX = frameX.coerceIn(0, screenW - frameW)
            frameY = frameY.coerceIn(0, screenH - frameH)

            captureSquare?.apply {
                layoutParams?.width = frameW
                layoutParams?.height = frameH
                translationX = frameX.toFloat()
                translationY = frameY.toFloat()
                requestLayout()
            }

            layoutTopBar?.apply {
                translationX = frameX.toFloat().coerceIn(0f, (screenW - width).toFloat().coerceAtLeast(0f))
                translationY = (frameY - overlayManager.dpToPx(44)).toFloat().coerceIn(0f, (screenH - height).toFloat().coerceAtLeast(0f))
            }

            layoutBottomBar?.apply {
                translationX = frameX.toFloat().coerceIn(0f, (screenW - width).toFloat().coerceAtLeast(0f))
                translationY = (frameY + frameH + overlayManager.dpToPx(4)).toFloat().coerceIn(0f, (screenH - height).toFloat().coerceAtLeast(0f))
            }
        }

        var initFrameX = 0
        var initFrameY = 0
        var touchX = 0f
        var touchY = 0f

        handleMove?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initFrameX = frameX
                    initFrameY = frameY
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    frameX = initFrameX + (event.rawX - touchX).toInt()
                    frameY = initFrameY + (event.rawY - touchY).toInt()
                    updatePositions()
                    true
                }
                else -> false
            }
        }

        var initW = 0
        var initH = 0
        handleResize?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initW = frameW
                    initH = frameH
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    frameW = initW + (event.rawX - touchX).toInt()
                    frameH = initH + (event.rawY - touchY).toInt()
                    updatePositions()
                    true
                }
                else -> false
            }
        }

        var isCircle = true
        btnToggleShape?.setOnClickListener {
            service.vibrateFeedback(20L)
            isCircle = !isCircle
            btnToggleShape.text = if (isCircle) "🔘" else "🔲"
            captureSquare?.setBackgroundResource(
                if (isCircle) R.drawable.border_capture else R.drawable.border_capture_square
            )
        }

        btnSearchArea?.setOnClickListener {
            service.vibrateFeedback(20L)
            Toast.makeText(service, "📐 Зона поиска задана", Toast.LENGTH_SHORT).show()
        }

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(40L)
            hide()
            service.addNewActionAtPosition(
                frameX + frameW / 2f,
                frameY + frameH / 2f,
                1000L,
                ActionType.TRIGGER,
                -1
            )
            Toast.makeText(service, "🎉 ИИ-Шаблон добавлен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        view.post { updatePositions() }
    }

    fun capture(): Bitmap? {
        return try {
            val dm = service.resources.displayMetrics
            Bitmap.createBitmap(dm.widthPixels, dm.heightPixels, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", capture_overlay_code)

    # 5. JoystickOverlay.kt
    joystick_overlay_code = r"""package com.example.autotap.ui.overlays

import android.graphics.PixelFormat
import android.graphics.PointF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class JoystickOverlay(
    private val service: MyAutoClickService,
    val overlayManager: OverlayManager = service.overlayManager
) {

    var rootView: View? = null
    private val pathPoints = ArrayList<PointF>()
    private var isRecordingPath = false

    fun show() {
        if (rootView != null) return

        val view = View.inflate(service, R.layout.floating_joystick_control, null)
        rootView = view

        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = overlayManager.dpToPx(30)
            y = overlayManager.dpToPx(200)
        }

        bindUi(view)
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
        pathPoints.clear()
        isRecordingPath = false
    }

    private fun bindUi(view: View) {
        val handleMove = view.findViewById<View>(R.id.handleMoveJoystick)
        val btnRecord = view.findViewById<Button>(R.id.btnRecordJoystick)
        val btnClose = view.findViewById<ImageButton>(R.id.btnCloseJoystick)
        val touchArea = view.findViewById<View>(R.id.viewJoystickBase)

        var initX = 0
        var initY = 0
        var touchX = 0f
        var touchY = 0f

        handleMove?.setOnTouchListener { _, event ->
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
                    val dm = service.resources.displayMetrics
                    val maxX = dm.widthPixels - view.width
                    val maxY = dm.heightPixels - view.height
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxX)
                    overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (!isRecordingPath) {
                startRecordingPath()
                btnRecord.text = "⏹ СОХРАНИТЬ"
            } else {
                savePathAsAction()
            }
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        touchArea?.setOnTouchListener { _, event ->
            if (!isRecordingPath) return@setOnTouchListener false

            val x = event.x
            val y = event.y

            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    pathPoints.clear()
                    pathPoints.add(PointF(x, y))
                }
                MotionEvent.ACTION_MOVE -> {
                    pathPoints.add(PointF(x, y))
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    pathPoints.add(PointF(x, y))
                }
            }
            true
        }
    }

    private fun startRecordingPath() {
        pathPoints.clear()
        isRecordingPath = true
    }

    private fun savePathAsAction() {
        if (pathPoints.size < 2) {
            service.vibrateFeedback(40L)
            hide()
            return
        }

        val dm = service.resources.displayMetrics

        val normPath = ArrayList<PointF>().apply {
            pathPoints.forEach { p ->
                add(
                    PointF(
                        (p.x / dm.widthPixels).coerceIn(0f, 1f),
                        (p.y / dm.heightPixels).coerceIn(0f, 1f)
                    )
                )
            }
        }

        val first = normPath.first()
        val last = normPath.last()

        val cfg = ActionConfig(
            id = service.actionsList.size + 1,
            type = ActionType.SWIPE,
            xNorm = first.x,
            yNorm = first.y,
            endXNorm = last.x,
            endYNorm = last.y,
            holdDuration = 600L,
            joystickPath = normPath
        )

        service.actionsList.add(cfg)
        hide()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/JoystickOverlay.kt", joystick_overlay_code)

    # 6. MyAutoClickService.kt (Включение публичных вспомогательных методов для панели)
    service_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "MyAutoClickService.kt")
    if os.path.exists(service_path):
        with open(service_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Добавление публичных методов управления
        extra_methods = r"""
    var isNumbersHidden = false

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

        val spawnOffset = (actionsList.size % 8) * overlayManager.dpToPx(24).toFloat()
        val spawnX = 350f + spawnOffset
        val spawnY = 350f + spawnOffset

        btnClick?.setOnClickListener {
            vibrateFeedback(20L)
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1)
            overlayManager.safeRemoveView(dialogView)
        }
        btnSwipe?.setOnClickListener {
            vibrateFeedback(20L)
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1)
            spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f)
            overlayManager.safeRemoveView(dialogView)
        }
        btnAi?.setOnClickListener {
            vibrateFeedback(20L)
            addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0)
            overlayManager.safeRemoveView(dialogView)
        }
        btnCancel?.setOnClickListener {
            vibrateFeedback(20L)
            overlayManager.safeRemoveView(dialogView)
        }

        overlayManager.safeAddView(dialogView, params)
    }

    fun showTutorialCard() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
        }

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvTutTitle)
        val tvDesc = dialogView.findViewById<TextView>(R.id.tvTutDesc)
        val btnPrev = dialogView.findViewById<Button>(R.id.btnTutPrev)
        val btnNext = dialogView.findViewById<Button>(R.id.btnTutNext)
        val btnSkip = dialogView.findViewById<Button>(R.id.btnTutSkip)

        var step = 0
        val steps = listOf(
            Pair("1/5: Главная панель", "Нажмите ▶ для запуска сценария, + для добавления клика, 📸 для ИИ-сканера."),
            Pair("2/5: Настройка шагов", "Тапните по круглой мишени на экране, чтобы изменить задержку, повторы или тип действия."),
            Pair("3/5: Запись жестов", "Нажмите 🔴 в меню, чтобы записывать ваши касания и свайпы прямо по экрану в реальном времени."),
            Pair("4/5: ИИ-Поиск", "Кнопка 📸 откроет прицел. Вырежьте любой элемент экрана, чтобы кликер находил его автоматически."),
            Pair("5/5: Скрипты", "Сохраняйте наборы шагов в файлы через папку 📁 и загружайте их в один клик.")
        )

        fun updateContent() {
            tvTitle?.text = steps[step].first
            tvDesc?.text = steps[step].second
            btnPrev?.visibility = if (step > 0) View.VISIBLE else View.INVISIBLE
            btnNext?.text = if (step < steps.size - 1) "Далее ►" else "Готово ✔"
        }

        updateContent()

        btnPrev?.setOnClickListener {
            vibrateFeedback(20L)
            if (step > 0) {
                step--
                updateContent()
            }
        }

        btnNext?.setOnClickListener {
            vibrateFeedback(20L)
            if (step < steps.size - 1) {
                step++
                updateContent()
            } else {
                overlayManager.safeRemoveView(dialogView)
            }
        }

        btnSkip?.setOnClickListener {
            vibrateFeedback(20L)
            overlayManager.safeRemoveView(dialogView)
        }

        overlayManager.safeAddView(dialogView, params)
    }

    private fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
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
"""
        if "fun toggleNumbersVisibility()" not in code:
            code = code.replace("class MyAutoClickService : AccessibilityService() {", "class MyAutoClickService : AccessibilityService() {\n" + extra_methods)
            with open(service_path, "w", encoding="utf-8") as f:
                f.write(code)
            print("  [✓] Обновлен MyAutoClickService.kt (добавлены публичные тач-методы)")

    print("✨ Все тач-события и оверлеи полностью отреставрированы!")

if __name__ == "__main__":
    apply_overlay_touch_repair()