package com.example.autotap.ui.overlays

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

class ScriptsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.5f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_scripts, null)

        view.bindClickByNames("btn_save_script", "btnSaveScript", "btn_save", "btnSave") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.saveScriptByName("default_script", svc.actionsList)
                logDiagnostic("SCRIPT", "Сценарий 'default_script' сохранен")
            }
            hide()
        }

        view.bindClickByNames("btn_close_dialog", "btnCloseDialog", "btn_close", "btnClose") {
            hide()
        }

        return view
    }
}
