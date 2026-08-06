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
import com.example.autotap.ui.overlays.PermissionsDialog
import com.example.autotap.ui.overlays.SaveRecordingDialog
import com.example.autotap.ui.overlays.ScriptsDialog
import com.example.autotap.ui.overlays.SearchAreaOverlay
import com.example.autotap.ui.overlays.TargetMarkerOverlay
import com.example.autotap.ui.overlays.TemplatesManagerDialog
import com.example.autotap.ui.overlays.TutorialOverlay

class OverlayManager(val context: Context) {

    private val overlays = mutableMapOf<OverlayLayer, OverlayBase>()

    val controlPanel by lazy { ControlPanelOverlay(context, this) }
    val debuggerOverlay by lazy { ScenarioDebuggerOverlay(context, this) }
    val candidateOverlay by lazy { CandidateSelectionOverlay(context, this) }
    val joystickOverlay by lazy { JoystickOverlay(context) }
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
    val permissionsDialog by lazy { PermissionsDialog(context, this) }
    val saveRecordingDialog by lazy { SaveRecordingDialog(context, this) }
    val searchAreaOverlay by lazy { SearchAreaOverlay(context) }
    val targetMarkerOverlay by lazy { TargetMarkerOverlay(context) }

    init {
        register(OverlayLayer.PANEL_LAYER, controlPanel)
        register(OverlayLayer.CAPTURE_LAYER, captureFrameOverlay)
        register(OverlayLayer.JOYSTICK_LAYER, joystickOverlay)
        register(OverlayLayer.DEBUG_LAYER, debuggerOverlay)
        register(OverlayLayer.TUTORIAL_LAYER, tutorialOverlay)
        register(OverlayLayer.DIALOG_LAYER, editActionDialog)
        register(OverlayLayer.SEARCH_AREA_LAYER, searchAreaOverlay)
        register(OverlayLayer.TARGET_LAYER, targetMarkerOverlay)
        register(OverlayLayer.STOP_BUTTON_LAYER, floatingStopButton)
        logDiagnostic("OVERLAY", "OverlayManager v40 полностью скомпонован.")
    }

    fun register(layer: OverlayLayer, overlay: OverlayBase) {
        overlays[layer] = overlay
        logDiagnostic("OVERLAY", "Зарегистрирован слой $layer")
    }

    fun show(layer: OverlayLayer) {
        overlays[layer]?.show()
    }

    fun hide(layer: OverlayLayer) {
        overlays[layer]?.hide()
    }

    fun getOverlay(layer: OverlayLayer): OverlayBase? {
        return overlays[layer]
    }

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

    fun setTouchable(layer: OverlayLayer, enabled: Boolean) {
        overlays[layer]?.setTouchable(enabled)
    }

    fun hideAll() {
        overlays.values.forEach { it.hide() }
    }
}
