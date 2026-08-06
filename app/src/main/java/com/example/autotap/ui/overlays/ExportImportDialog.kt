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

class ExportImportDialog(context: Context, overlayManager: OverlayManager) :
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
        val view = inflater.inflate(R.layout.dialog_export_select, null)

        try {
            inflater.inflate(R.layout.dialog_select_script_for_export, null)
            inflater.inflate(R.layout.item_script, null)
        } catch (_: Exception) {}

        view.bindClickByNames("btnCloseExpSelect") {
            hide()
        }

        view.bindClickByNames("btnExpFullBackup") {
            val svc = MyAutoClickService.instance
            svc?.saveScriptByName("full_backup", svc.actionsList)
            logDiagnostic("SCRIPT", "Создан полный бэкап через btnExpFullBackup.")
            hide()
        }

        view.bindClickByNames("btnExpSingleScript", "btnExpChainScripts", "btnExpTemplatesOnly") {
            logDiagnostic("SCRIPT", "Экспорт выбранного типа сценария.")
            hide()
        }

        return view
    }
}
