package com.example.autotap.ui.overlays

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_control_panel, null)

        view.bindClickByNames("btn_play", "btnPlay", "btn_start", "btnStart", "play", "ic_play", "start") {
            logDiagnostic("OVERLAY", "Кнопка СТАРТ нажата в оригинальной XML-панели.")
            MyAutoClickService.instance?.scriptExecutor?.start()
        }

        view.bindClickByNames("btn_add", "btnAdd", "add", "ic_add", "btn_add_action") {
            logDiagnostic("OVERLAY", "Кнопка +ДЕЙСТВИЕ нажата в оригинальной XML-панели.")
            overlayManager.captureFrameOverlay.show()
        }

        view.bindClickByNames("btn_scripts", "btnScripts", "scripts", "ic_folder", "dialog_scripts") {
            logDiagnostic("OVERLAY", "Кнопка СЦЕНАРИИ нажата в оригинальной XML-панели.")
            overlayManager.scriptsDialog.show()
        }

        view.bindClickByNames("btn_settings", "btnSettings", "settings", "ic_settings") {
            logDiagnostic("OVERLAY", "Кнопка НАСТРОЙКИ нажата в оригинальной XML-панели.")
            overlayManager.globalSettingsDialog.show()
        }

        view.bindClickByNames("btn_help", "btnHelp", "help", "ic_help") {
            logDiagnostic("OVERLAY", "Кнопка СПРАВКА нажата в оригинальной XML-панели.")
            overlayManager.infoHelpDialog.show()
        }

        view.bindClickByNames("btn_close", "btnClose", "btn_stop", "btnStop", "ic_close", "close", "stop") {
            logDiagnostic("OVERLAY", "Кнопка СТОП/ЗАКРЫТЬ нажата в оригинальной XML-панели.")
            MyAutoClickService.instance?.scriptExecutor?.stop()
            hide()
        }

        setupDragAndDrop(view)
        return view
    }
}
