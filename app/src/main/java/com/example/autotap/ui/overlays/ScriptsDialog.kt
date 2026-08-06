package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ScriptsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var etNameView: EditText? = null
    private var etLoopCountView: EditText? = null
    private var isInfiniteLoop = true

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

        etNameView = view.findViewByNames("etScriptName") as? EditText
        etLoopCountView = view.findViewByNames("etScriptLoopCount") as? EditText

        view.bindClickByNames("btnSaveScriptAction") {
            val scriptName = etNameView?.text?.toString()?.ifBlank { "default_script" } ?: "default_script"
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.saveScriptByName(scriptName, svc.actionsList)
                logDiagnostic("SCRIPT", "Сценарий '$scriptName' сохранен по btnSaveScriptAction")
            }
            hide()
        }

        view.bindClickByNames("btnToggleScriptInfinite") { btn ->
            isInfiniteLoop = !isInfiniteLoop
            btn.isSelected = isInfiniteLoop
            (btn as? Button)?.apply {
                text = if (isInfiniteLoop) "Бесконечный повтор: [ ВКЛ ]" else "Бесконечный повтор: [ ВЫКЛ ]"
                setTextColor(if (isInfiniteLoop) Color.parseColor("#00E676") else Color.WHITE)
            }
            logDiagnostic("SCRIPT", "Переключение бесконечного повтора: $isInfiniteLoop")
        }

        view.bindClickByNames("btnSelectScriptRelay") {
            logDiagnostic("SCRIPT", "Выбор эстафетного сценария.")
        }

        view.bindClickByNames("btnCloseScripts", "btnCloseScriptsHeader") {
            hide()
        }

        return view
    }
}
