import os
import sys

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

files = {}

# 1. OverlayBase.kt — Согласование конструктора (context, overlayManager) и свойства open val layoutResId
files["app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt"] = """package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Rect
import android.os.Build
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import androidx.core.view.ViewCompat
import com.example.autotap.createOverlayParams
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.safeAddView
import com.example.autotap.safeRemoveView
import kotlin.math.abs

abstract class OverlayBase(
    protected val context: Context,
    val overlayManager: OverlayManager
) {
    protected val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    open val layoutResId: Int = 0

    var width: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var height: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var gravity: Int = Gravity.TOP or Gravity.START
    var flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
    var dimAmount: Float = 0.5f

    var initialX: Int = 100
    var initialY: Int = 200

    var layer: OverlayLayer = OverlayLayer.PANEL_LAYER
    var priority: OverlayPriority = OverlayPriority.MEDIUM

    protected var overlayView: View? = null
    protected var rootView: View? = null
    protected var layoutParams: WindowManager.LayoutParams? = null
    protected var params: WindowManager.LayoutParams? = null
    var isShowing: Boolean = false
        protected set

    private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop

    open fun createView(): View {
        if (layoutResId != 0) {
            return LayoutInflater.from(context).inflate(layoutResId, null)
        }
        throw UnsupportedOperationException("Оверлей должен переопределить layoutResId или createView()")
    }

    open fun inflate() {
        if (rootView != null) return
        val view = createView()
        rootView = view
        overlayView = view

        val lp = createOverlayParams(
            width = width,
            height = height,
            gravity = gravity,
            flags = flags,
            x = initialX,
            y = initialY
        ).apply {
            if (this@OverlayBase.dimAmount > 0f && (flags and WindowManager.LayoutParams.FLAG_DIM_BEHIND) != 0) {
                this.dimAmount = this@OverlayBase.dimAmount
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                this.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        this.layoutParams = lp
        this.params = lp
        ViewCompat.setImportantForAccessibility(
            view,
            ViewCompat.IMPORTANT_FOR_ACCESSIBILITY_NO
        )
    }

    open fun show() {
        if (isShowing && overlayView != null) {
            try {
                windowManager.safeRemoveView(overlayView!!)
            } catch (_: Exception) {}
            isShowing = false
        }

        try {
            inflate()
            val view = overlayView ?: rootView ?: return
            val lp = layoutParams ?: params ?: return
            reboundToScreen(lp)
            val added = windowManager.safeAddView(view, lp)
            if (added) {
                isShowing = true
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) принудительно отображен.")
            }
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка при отображении ${javaClass.simpleName}", e)
        }
    }

    open fun hide() {
        val view = overlayView ?: rootView ?: return
        if (isShowing) {
            try {
                windowManager.safeRemoveView(view)
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} скрыт.")
            } catch (e: Exception) {
                logError("OVERLAY", "Ошибка при скрытии ${javaClass.simpleName}", e)
            }
            overlayView = null
            rootView = null
            isShowing = false
        }
    }

    fun reboundToScreen(lp: WindowManager.LayoutParams) {
        val screenSize = context.getRealScreenSize()
        val maxX = (screenSize.x - 100).coerceAtLeast(10)
        val maxY = (screenSize.y - 100).coerceAtLeast(10)
        lp.x = lp.x.coerceIn(0, maxX)
        lp.y = lp.y.coerceIn(0, maxY)
    }

    fun updatePosition(x: Int, y: Int) {
        val lp = layoutParams ?: params ?: return
        val screenSize = context.getRealScreenSize()
        lp.x = x.coerceIn(0, (screenSize.x - 100).coerceAtLeast(10))
        lp.y = y.coerceIn(0, (screenSize.y - 100).coerceAtLeast(10))
        val v = overlayView ?: rootView ?: return
        try {
            windowManager.updateViewLayout(v, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления позиции $layer", e)
        }
    }

    fun setTouchable(touchable: Boolean) {
        val lp = layoutParams ?: params ?: return
        val view = overlayView ?: rootView ?: return
        if (touchable) {
            lp.flags = lp.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
        } else {
            lp.flags = lp.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
        }
        try {
            windowManager.updateViewLayout(view, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления флага touchable", e)
        }
    }

    fun getBounds(): Rect {
        val lp = layoutParams ?: params ?: return Rect(0, 0, 0, 0)
        val w = if (width > 0) width else 200
        val h = if (height > 0) height else 200
        return Rect(lp.x, lp.y, lp.x + w, lp.y + h)
    }

    protected fun setupDragAndDrop(handleView: View) {
        var startX = 0
        var startY = 0
        var touchX = 0f
        var touchY = 0f
        var isDragging = false

        handleView.setOnTouchListener { v, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = lp.x
                    startY = lp.y
                    touchX = event.rawX
                    touchY = event.rawY
                    isDragging = false
                    false
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    if (!isDragging && (abs(dx) > touchSlop || abs(dy) > touchSlop)) {
                        isDragging = true
                    }

                    if (isDragging) {
                        val newX = startX + dx
                        val newY = startY + dy
                        updatePosition(newX, newY)
                        true
                    } else {
                        false
                    }
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    if (isDragging) {
                        isDragging = false
                        true
                    } else {
                        false
                    }
                }
                else -> false
            }
        }
    }
}
"""

# 2. ControlPanelOverlay.kt — Передача (context, overlayManager) в super
files["app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    override val layoutResId: Int = R.layout.floating_control_panel

    private var btnPlayView: View? = null
    private var btnRecordView: View? = null
    private var btnJoystickView: View? = null
    private var panelState = 0

    init {
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        btnPlayView = view.findViewByNames("btnPlay")
        btnRecordView = view.findViewByNames("btnRecord")
        btnJoystickView = view.findViewByNames("btnToggleJoystick")

        view.bindClickByNames("btnToggleMenu", "btnSingleBubble") {
            cyclePanelState(view)
        }

        view.bindClickByNames("btnCapturePool") {
            logDiagnostic("OVERLAY", "Запуск прицела вырезания шаблона по btnCapturePool.")
            context.vibrateFeedback()
            overlayManager.captureFrameOverlay.show()
        }

        view.bindClickByNames("btnAdd") {
            logDiagnostic("OVERLAY", "Открытие меню добавления действия по btnAdd.")
            context.vibrateFeedback()
            overlayManager.addActionDialog.show()
        }

        view.bindClickByNames("btnPlay") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                if (svc.isPlaying) {
                    svc.scriptExecutor.stop()
                } else {
                    svc.scriptExecutor.start()
                }
                updateToggleStates()
            }
        }

        view.bindClickByNames("btnRecord") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                if (svc.recordingEngine.isRecording) {
                    svc.recordingEngine.stopRecording("recorded_script")
                } else {
                    svc.recordingEngine.startRecording()
                }
                updateToggleStates()
            }
        }

        view.bindClickByNames("btnClearAll") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.actionsList.clear()
                context.vibrateFeedback()
                logDiagnostic("OVERLAY", "Очищены все шаги сценария.")
            }
        }

        view.bindClickByNames("btnLoadScript") {
            logDiagnostic("OVERLAY", "Кнопка btnLoadScript нажата.")
            overlayManager.scriptsDialog.show()
        }

        view.bindClickByNames("btnToggleJoystick") {
            if (overlayManager.joystickOverlay.isShowing) {
                overlayManager.joystickOverlay.hide()
            } else {
                overlayManager.joystickOverlay.show()
            }
            updateToggleStates()
        }

        view.bindClickByNames("btnHelpTutorial") {
            logDiagnostic("OVERLAY", "Кнопка btnHelpTutorial нажата.")
            MyAutoClickService.instance?.tutorialEngine?.startDefaultTutorial()
        }

        view.bindClickByNames("btnClose") {
            logDiagnostic("OVERLAY", "Кнопка btnClose нажата.")
            MyAutoClickService.instance?.scriptExecutor?.stop()
            hide()
        }

        val dragHandle = view.findViewByNames("handleDrag") ?: view
        setupDragAndDrop(dragHandle)
        updateToggleStates()
        return view
    }

    private fun cyclePanelState(root: View) {
        panelState = (panelState + 1) % 3
        val mainRow = root.findViewByNames("layoutMainRow")
        val subMenu = root.findViewByNames("layoutSubMenu")
        val mainCard = root.findViewByNames("layoutMainCard")
        val singleBubble = root.findViewByNames("btnSingleBubble")

        val lp = layoutParams ?: params ?: return

        when (panelState) {
            0 -> {
                lp.width = WindowManager.LayoutParams.WRAP_CONTENT
                lp.height = WindowManager.LayoutParams.WRAP_CONTENT
                mainCard?.visibility = View.VISIBLE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.VISIBLE
                singleBubble?.visibility = View.GONE
                logDiagnostic("OVERLAY", "Панель: Режим 2 строки (Full)")
            }
            1 -> {
                val bubbleSizePx = 56.dpToPx(context)
                lp.width = bubbleSizePx
                lp.height = bubbleSizePx
                mainCard?.visibility = View.GONE
                mainRow?.visibility = View.GONE
                subMenu?.visibility = View.GONE
                singleBubble?.visibility = View.VISIBLE
                logDiagnostic("OVERLAY", "Панель: Режим Одиночный Шарик (Bubble ${bubbleSizePx}px)")
            }
            2 -> {
                lp.width = WindowManager.LayoutParams.WRAP_CONTENT
                lp.height = WindowManager.LayoutParams.WRAP_CONTENT
                mainCard?.visibility = View.VISIBLE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.GONE
                singleBubble?.visibility = View.GONE
                logDiagnostic("OVERLAY", "Панель: Режим 1 строка (Compact)")
            }
        }

        try {
            windowManager.updateViewLayout(overlayView ?: rootView, lp)
        } catch (e: Exception) {
            logDiagnostic("OVERLAY", "Ошибка обновления размера окна при сворачивании.")
        }
        context.vibrateFeedback()
    }

    fun updateToggleStates() {
        val svc = MyAutoClickService.instance

        (btnPlayView as? Button)?.apply {
            val isPlaying = svc?.isPlaying == true
            isSelected = isPlaying
            text = if (isPlaying) "[ РАБОТАЕТ... ]" else "СТАРТ"
            setTextColor(if (isPlaying) Color.parseColor("#00E676") else Color.WHITE)
        }

        (btnRecordView as? Button)?.apply {
            val isRecording = svc?.recordingEngine?.isRecording == true
            isSelected = isRecording
            text = if (isRecording) "[ ЗАПИСЬ... ]" else "ЗАПИСЬ"
            setTextColor(if (isRecording) Color.parseColor("#FF5252") else Color.WHITE)
        }

        (btnJoystickView as? Button)?.apply {
            val isJoystickVisible = overlayManager.joystickOverlay.isShowing
            isSelected = isJoystickVisible
            text = if (isJoystickVisible) "[ ДЖОЙСТИК: ВКЛ ]" else "ДЖОЙСТИК"
            setTextColor(if (isJoystickVisible) Color.parseColor("#00E676") else Color.WHITE)
        }
    }
}
"""

# 3. CaptureFrameOverlay.kt — Передача (context, overlayManager) в super
files["app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 24.dpToPx(context)
    private var currentFrameWidthPx = 240.dpToPx(context)
    private var currentFrameHeightPx = 240.dpToPx(context)

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = currentFrameWidthPx
        height = currentFrameHeightPx
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски с экрана (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val lp = layoutParams ?: params
            if (svc != null && lp != null) {
                val metrics = context.resources.displayMetrics
                val centerXNorm = (lp.x + currentFrameWidthPx / 2f) / metrics.widthPixels.toFloat()
                val centerYNorm = (lp.y + currentFrameHeightPx / 2f) / metrics.heightPixels.toFloat()

                val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                val action = ActionConfig(
                    type = ActionType.AI_SEARCH,
                    xNorm = centerXNorm.coerceIn(0f, 1f),
                    yNorm = centerYNorm.coerceIn(0f, 1f),
                    selectedTemplateIndex = nextTemplateIndex
                )
                svc.actionsList.add(action)

                val fullBitmap = svc.captureScreenBitmap()
                if (fullBitmap != null && fullBitmap.width > 20 && fullBitmap.height > 20) {
                    val safeX = lp.x.coerceIn(0, (fullBitmap.width - 20).coerceAtLeast(0))
                    val safeY = lp.y.coerceIn(0, (fullBitmap.height - 20).coerceAtLeast(0))
                    val safeW = currentFrameWidthPx.coerceIn(10, fullBitmap.width - safeX)
                    val safeH = currentFrameHeightPx.coerceIn(10, fullBitmap.height - safeY)

                    if (safeW > 10 && safeH > 10) {
                        val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                        svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)
                        logDiagnostic("AI_SCANNER", "Безопасный кроп: шаблон #$nextTemplateIndex сохранен (${safeW}x${safeH}px).")
                    }
                }
            }
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCancelCapture", "btn_cancel_capture", "btn_close") {
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCaptureSearchArea") {
            logDiagnostic("OVERLAY", "Переход к настройке области поиска.")
            overlayManager.searchAreaOverlay.show()
            hide()
        }

        val moveHandle = view.findViewByNames("handleMoveFrame", "layoutTopBar", "layoutCaptureContainer") ?: view
        setupDragAndDrop(moveHandle)

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null) {
            setupResizeHandler(resizeHandle)
        }

        return view
    }

    private fun setupResizeHandler(resizeView: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = lp.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = lp.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    currentFrameWidthPx = max(minSizePx, startW + dx)
                    currentFrameHeightPx = max(minSizePx, startH + dy)

                    lp.width = currentFrameWidthPx
                    lp.height = currentFrameHeightPx
                    width = currentFrameWidthPx
                    height = currentFrameHeightPx

                    try {
                        windowManager.updateViewLayout(overlayView ?: rootView, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка ресайза прицела", e)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
"""

print("=== ФИКС createView И КЛИЕНТСКИХ ОВЕРЛЕЕВ ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ОШИБКИ УСПЕШНО УСТРАНЕНЫ ===")