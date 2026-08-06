package com.example.autotap.ui.overlays

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

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var btnPlayView: View? = null
    private var btnRecordView: View? = null
    private var btnJoystickView: View? = null

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

        view.bindClickByNames("btnAdd") {
            logDiagnostic("OVERLAY", "Кнопка btnAdd нажата.")
            overlayManager.addActionDialog.show()
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
