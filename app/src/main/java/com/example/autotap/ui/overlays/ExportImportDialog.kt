package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.findViewByNames
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
        val inflatedView = try {
            inflater.inflate(R.layout.dialog_export_select, null)
        } catch (e: Exception) {
            null
        }

        val root = inflatedView ?: LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            setPadding(32, 32, 32, 32)

            addView(Button(context).apply {
                text = "Экспорт сценария"
                setOnClickListener {
                    val svc = MyAutoClickService.instance
                    if (svc != null) {
                        svc.saveScriptByName("exported_script", svc.actionsList)
                    }
                    hide()
                }
            })
            addView(Button(context).apply {
                text = "Закрыть"
                setOnClickListener { hide() }
            })
        }

        root.findViewByNames("btn_export", "btnExport", "btn_save")?.setOnClickListener {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.saveScriptByName("exported_script", svc.actionsList)
                logDiagnostic("SCRIPT", "Сценарий экспортирован через ExportImportDialog.")
            }
            hide()
        }

        root.findViewByNames("btn_cancel", "btnCancel", "btn_close", "btnClose")?.setOnClickListener {
            hide()
        }

        return root
    }
}
