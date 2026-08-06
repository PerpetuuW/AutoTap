package com.example.autotap.ui.base

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.CandidateSelectionOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ClickVisualizerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.ScriptsDialog

class OverlayManager(val context: Context) {

    val controlPanel by lazy { ControlPanelOverlay(context, this) }
    val debuggerOverlay by lazy { ScenarioDebuggerOverlay(context, this) }
    val candidateOverlay by lazy { CandidateSelectionOverlay(context, this) }
    val joystickOverlay by lazy { JoystickOverlay(context, this) }
    val editActionDialog by lazy { EditActionDialog(context, this) }
    val captureFrameOverlay by lazy { CaptureFrameOverlay(context, this) }
    val scriptsDialog by lazy { ScriptsDialog(context, this) }
    val clickVisualizer by lazy { ClickVisualizerOverlay(context, this) }

    fun showControlPanel() {
        controlPanel.show()
    }

    fun hideControlPanel() {
        controlPanel.hide()
    }

    fun showFloatingStopButton() {
        logDiagnostic("OVERLAY", "Отображена плавающая кнопка СТОП.")
    }

    fun hideFloatingStopButton() {
        logDiagnostic("OVERLAY", "Скрыта плавающая кнопка СТОП.")
    }

    fun showClickVisualizer(x: Float, y: Float) {
        clickVisualizer.showClickAt(x, y)
    }

    fun hideAll() {
        controlPanel.hide()
        debuggerOverlay.hide()
        candidateOverlay.hide()
        joystickOverlay.hide()
        editActionDialog.hide()
        captureFrameOverlay.hide()
        scriptsDialog.hide()
        clickVisualizer.hide()
    }
}
