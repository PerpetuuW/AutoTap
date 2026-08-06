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

    forbidden = ["TODO()", "// остальной код", "// TODO"]
    for item in forbidden:
        if item in content:
            raise ValueError(f"Обнаружена запрещенная заглушка '{item}' в файле {filename}")

files = {}

# 1. OverlayBase.kt — Гарантированное отображение show() со сбросом старых видов
files["app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt"] = """package com.example.autotap.ui.base

import android.content.Context
import android.graphics.Rect
import android.os.Build
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import com.example.autotap.createOverlayParams
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
    protected var layoutParams: WindowManager.LayoutParams? = null
    var isShowing: Boolean = false
        protected set

    private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop

    abstract fun createView(): View

    open fun show() {
        if (isShowing && overlayView != null) {
            try {
                windowManager.safeRemoveView(overlayView!!)
            } catch (_: Exception) {}
            isShowing = false
        }

        try {
            val view = createView()
            view.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            overlayView = view
            val params = createOverlayParams(
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
            this.layoutParams = params
            val added = windowManager.safeAddView(view, params)
            if (added) {
                isShowing = true
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) принудительно отображен.")
            }
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка при отображении ${javaClass.simpleName}", e)
        }
    }

    open fun hide() {
        val view = overlayView ?: return
        if (isShowing) {
            try {
                windowManager.safeRemoveView(view)
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} скрыт.")
            } catch (e: Exception) {
                logError("OVERLAY", "Ошибка при скрытии ${javaClass.simpleName}", e)
            }
            overlayView = null
            isShowing = false
        }
    }

    fun setTouchable(touchable: Boolean) {
        val lp = layoutParams ?: return
        val view = overlayView ?: return
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
        val lp = layoutParams ?: return Rect(0, 0, 0, 0)
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
            val lp = layoutParams ?: return@setOnTouchListener false
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
                        lp.x = startX + dx
                        lp.y = startY + dy
                        try {
                            windowManager.updateViewLayout(overlayView ?: v, lp)
                        } catch (e: Exception) {
                            logError("OVERLAY", "Ошибка перемещения оверлея", e)
                        }
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

# 2. ControlPanelOverlay.kt — Прямой запуск прицела по btnCapturePool и btnAdd
files["app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var btnPlayView: View? = null
    private var btnRecordView: View? = null
    private var btnJoystickView: View? = null
    private var panelState = 0 // 0 = 2 строки (Full), 1 = 1 строка (Compact), 2 = 1 кнопка (Bubble)

    init {
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_control_panel, null)

        btnPlayView = view.findViewByNames("btnPlay")
        btnRecordView = view.findViewByNames("btnRecord")
        btnJoystickView = view.findViewByNames("btnToggleJoystick")

        // 3-Этапный циклический режим сворачивания
        view.bindClickByNames("btnToggleMenu", "btnSingleBubble") {
            cyclePanelState(view)
        }

        // КНОПКА ПРИЦЕЛА И СОЗДАНИЯ ШАБЛОНА
        view.bindClickByNames("btnCapturePool", "btnAdd") {
            logDiagnostic("OVERLAY", "Запуск прицела вырезания шаблона (CaptureFrameOverlay).")
            context.vibrateFeedback()
            overlayManager.captureFrameOverlay.show()
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

        when (panelState) {
            0 -> { // 2 строки (Full)
                mainCard?.visibility = View.VISIBLE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.VISIBLE
                singleBubble?.visibility = View.GONE
                logDiagnostic("OVERLAY", "Панель: Режим 2 строки (Full)")
            }
            1 -> { // 1 строка (Compact)
                mainCard?.visibility = View.VISIBLE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.GONE
                singleBubble?.visibility = View.GONE
                logDiagnostic("OVERLAY", "Панель: Режим 1 строка (Compact)")
            }
            2 -> { // 1 кнопка (Bubble)
                mainCard?.visibility = View.GONE
                mainRow?.visibility = View.GONE
                subMenu?.visibility = View.GONE
                singleBubble?.visibility = View.VISIBLE
                logDiagnostic("OVERLAY", "Панель: Режим 1 кнопка (Single Bubble)")
            }
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

# 3. AddActionDialog.kt — Вызов прицела по btnAddTrigger / btnAddAi
files["app/src/main/java/com/example/autotap/ui/overlays/AddActionDialog.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class AddActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_add_action, null)

        view.bindClickByNames("btnAddClick") {
            MyAutoClickService.instance?.addNewActionAtPosition(0.5f, 0.5f)
            logDiagnostic("SCRIPT", "Добавлено действие КЛИК.")
            hide()
        }

        view.bindClickByNames("btnAddTrigger", "btnAddAi", "btnAddSwipe") {
            logDiagnostic("OVERLAY", "Открытие прицела захвата маски из AddActionDialog.")
            overlayManager.captureFrameOverlay.show()
            hide()
        }

        view.bindClickByNames("btnCancelAdd") {
            hide()
        }

        return view
    }
}
"""

print("=== ФИКС ПРЯМОГО ЗАПУСКА ПРИЦЕЛА И ОБНОВЛЕНИЯ show() ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ЗАПУСК ПРИЦЕЛА УСПЕШНО ИСПРАВЛЕН ===")