package com.example.autotap.ui.overlays

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

    private var btnPlayView: View? = null
    private var btnRecordView: View? = null
    private var btnJoystickView: View? = null
    private var panelState = 0 // 0 = Full (2 строки), 1 = Single Bubble (1 шарик), 2 = Compact (1 строка)

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

        val lp = layoutParams ?: return

        when (panelState) {
            0 -> { // 2 строки (Full)
                lp.width = WindowManager.LayoutParams.WRAP_CONTENT
                lp.height = WindowManager.LayoutParams.WRAP_CONTENT
                mainCard?.visibility = View.VISIBLE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.VISIBLE
                singleBubble?.visibility = View.GONE
                logDiagnostic("OVERLAY", "Панель: Режим 2 строки (Full)")
            }
            1 -> { // 1 кнопка (Single Bubble) - ФИКС: singleBubble виден!
                val bubbleSizePx = 56.dpToPx(context)
                lp.width = bubbleSizePx
                lp.height = bubbleSizePx
                mainCard?.visibility = View.GONE
                mainRow?.visibility = View.GONE
                subMenu?.visibility = View.GONE
                singleBubble?.visibility = View.VISIBLE
                logDiagnostic("OVERLAY", "Панель: Режим Одиночный Шарик (Bubble ${bubbleSizePx}px)")
            }
            2 -> { // 1 строка (Compact)
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
            windowManager.updateViewLayout(overlayView, lp)
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
