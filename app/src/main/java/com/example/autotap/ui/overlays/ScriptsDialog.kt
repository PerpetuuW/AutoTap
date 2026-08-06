package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScriptsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.5f
    }

    override fun createView(): View {
        return LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.DKGRAY)
            setPadding(24, 24, 24, 24)

            addView(TextView(context).apply {
                text = "Менеджер сценариев"
                setTextColor(Color.WHITE)
                textSize = 18f
            })

            addView(Button(context).apply {
                text = "Сохранить текущий сценарий"
                setOnClickListener {
                    val svc = MyAutoClickService.instance
                    if (svc != null) {
                        svc.saveScriptByName("default_script", svc.actionsList)
                        logDiagnostic("SCRIPT", "Сценарий 'default_script' сохранен")
                    }
                    hide()
                }
            })
        }
    }
}
