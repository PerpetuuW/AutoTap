package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.StructuredLogger
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
    private var btnHideNumbersView: View? = null

    private var displayStage = 0

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
        btnHideNumbersView = view.findViewByNames("btnHideNumbers")

        view.bindClickByNames("btnToggleMenu") {
            cycleDisplayStage(view)
        }

        view.bindClickByNames("btnSingleBubble") {
            cycleDisplayStage(view)
        }

        view.bindClickByNames("btnCapturePool") {
            StructuredLogger.logDiagnostic("OVERLAY", "Запуск прицела вырезания шаблона.")
            context.vibrateFeedback()
            overlayManager.captureFrameOverlay.show()
        }

        view.bindClickByNames("btnAdd") {
            StructuredLogger.logDiagnostic("OVERLAY", "Открытие меню добавления действия.")
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
                overlayManager.updateTargetMarkers()
                context.vibrateFeedback()
                StructuredLogger.logDiagnostic("OVERLAY", "Очищены все шаги сценария и мишени.")
            }
        }

        // 💥 ФИКС: Кнопка «Глаз» становится КРАСНОЙ только когда мишени СКРЫТЫ!
        view.bindClickByNames("btnHideNumbers") {
            overlayManager.toggleTargetMarkersVisibility()
            updateToggleStates()
            context.vibrateFeedback()
        }

        view.bindClickByNames("btnLoadScript") {
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
            MyAutoClickService.instance?.tutorialEngine?.startDefaultTutorial()
        }

        view.bindClickByNames("btnClose") {
            MyAutoClickService.instance?.scriptExecutor?.stop()
            hide()
        }

        val dragHandle = view.findViewByNames("handleDrag") ?: view
        setupDragAndDrop(dragHandle)
        updateToggleStates()
        return view
    }

    private fun cycleDisplayStage(root: View) {
        displayStage = (displayStage + 1) % 3
        val mainRow = root.findViewByNames("layoutMainRow")
        val subMenu = root.findViewByNames("layoutSubMenu")
        val singleBubble = root.findViewByNames("btnSingleBubble")

        val lp = layoutParams ?: params
        val targetView = overlayView ?: rootView

        when (displayStage) {
            0 -> {
                singleBubble?.visibility = View.GONE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.VISIBLE
                if (lp != null && targetView != null) {
                    lp.width = WindowManager.LayoutParams.WRAP_CONTENT
                    lp.height = WindowManager.LayoutParams.WRAP_CONTENT
                    reboundToScreen(lp)
                    try { windowManager.updateViewLayout(targetView, lp) } catch (_: Exception) {}
                }
            }
            1 -> {
                mainRow?.visibility = View.GONE
                subMenu?.visibility = View.GONE
                singleBubble?.visibility = View.VISIBLE
                if (lp != null && targetView != null) {
                    val bubbleSizePx = 44.dpToPx(context)
                    lp.width = bubbleSizePx
                    lp.height = bubbleSizePx
                    reboundToScreen(lp)
                    try { windowManager.updateViewLayout(targetView, lp) } catch (_: Exception) {}
                }
            }
            2 -> {
                singleBubble?.visibility = View.GONE
                mainRow?.visibility = View.VISIBLE
                subMenu?.visibility = View.GONE
                if (lp != null && targetView != null) {
                    lp.width = WindowManager.LayoutParams.WRAP_CONTENT
                    lp.height = WindowManager.LayoutParams.WRAP_CONTENT
                    reboundToScreen(lp)
                    try { windowManager.updateViewLayout(targetView, lp) } catch (_: Exception) {}
                }
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

        // 💥 ИНДИКАТОР ГЛАЗА: КРАСНЫЙ ФОН ТОЛЬКО ТОГДА, КОГДА МИШЕНИ СКРЫТЫ (areMarkersVisible == false)!
        (btnHideNumbersView as? ImageButton)?.apply {
            val areVisible = overlayManager.areMarkersVisible
            if (!areVisible) {
                setImageResource(R.drawable.ic_eye_off)
                setBackgroundResource(R.drawable.btn_premium_record) // КРАСНЫЙ ФОН: ВНИМАНИЕ, МИШЕНИ СКРЫТЫ!
            } else {
                setImageResource(R.drawable.ic_eye)
                setBackgroundResource(R.drawable.btn_premium_secondary) // ОБЫЧНЫЙ ТЕМНЫЙ ФОН: МИШЕНИ ВИДНЫ
            }
        }
    }
}
