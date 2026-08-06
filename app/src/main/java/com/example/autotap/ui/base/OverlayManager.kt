package com.example.autotap.ui.base

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.AddActionDialog
import com.example.autotap.ui.overlays.CandidateSelectionOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ClickVisualizerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.ExportImportDialog
import com.example.autotap.ui.overlays.FloatingStopButtonOverlay
import com.example.autotap.ui.overlays.GlobalSettingsDialog
import com.example.autotap.ui.overlays.InfoHelpDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.MaskEditorDialog
import com.example.autotap.ui.overlays.ScriptsDialog
import com.example.autotap.ui.overlays.TemplatesManagerDialog
import com.example.autotap.ui.overlays.TutorialOverlay

class OverlayManager(val context: Context) {

    val controlPanel by lazy { ControlPanelOverlay(context, this) }
    val debuggerOverlay by lazy { ScenarioDebuggerOverlay(context, this) }
    val candidateOverlay by lazy { CandidateSelectionOverlay(context, this) }
    val joystickOverlay by lazy { JoystickOverlay(context, this) }
    val editActionDialog by lazy { EditActionDialog(context, this) }
    val captureFrameOverlay by lazy { CaptureFrameOverlay(context, this) }
    val scriptsDialog by lazy { ScriptsDialog(context, this) }
    val clickVisualizer by lazy { ClickVisualizerOverlay(context, this) }
    val tutorialOverlay by lazy { TutorialOverlay(context, this) }
    val infoHelpDialog by lazy { InfoHelpDialog(context, this) }
    val templatesManagerDialog by lazy { TemplatesManagerDialog(context, this) }
    val globalSettingsDialog by lazy { GlobalSettingsDialog(context, this) }
    val maskEditorDialog by lazy { MaskEditorDialog(context, this) }
    val floatingStopButton by lazy { FloatingStopButtonOverlay(context, this) }
    val addActionDialog by lazy { AddActionDialog(context, this) }
    val exportImportDialog by lazy { ExportImportDialog(context, this) }

    fun showControlPanel() {
        controlPanel.show()
    }

    fun hideControlPanel() {
        controlPanel.hide()
    }

    fun showFloatingStopButton() {
        floatingStopButton.show()
    }

    fun hideFloatingStopButton() {
        floatingStopButton.hide()
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
        tutorialOverlay.hide()
        infoHelpDialog.hide()
        templatesManagerDialog.hide()
        globalSettingsDialog.hide()
        maskEditorDialog.hide()
        floatingStopButton.hide()
        addActionDialog.hide()
        exportImportDialog.hide()
    }
}
