package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class GlobalSettingsDialog(context: Context, overlayManager: OverlayManager) :
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
        val view = inflater.inflate(R.layout.dialog_global_settings, null)

        view.bindClickByNames("btn_save_settings", "btnSaveSettings", "btn_save", "btnSave") {
            logDiagnostic("UI", "Глобальные настройки сохранены.")
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btn_close_settings", "btnCloseSettings", "btn_close", "btnCancel") {
            hide()
        }

        return view
    }
}
