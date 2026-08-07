package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.EditText
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ScriptsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_scripts

    private var etScriptName: EditText? = null

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND
        dimAmount = 0.5f
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        etScriptName = view.findViewByNames("etScriptName") as? EditText

        view.bindClickByNames("btnSaveScriptAction") {
            val name = etScriptName?.text?.toString()?.takeIf { it.isNotBlank() } ?: "default_script"
            val svc = MyAutoClickService.instance
            svc?.saveScriptByName(name, svc.actionsList)
            hide()
        }

        view.bindClickByNames("btnCloseScripts", "btnCloseScriptsHeader") {
            hide()
        }

        return view
    }

    override fun show() {
        super.show()
        setFocusable(true) // ВЛЮЧАЕМ ФОКУС ДЛЯ РАБОТЫ КЛАВИАТУРЫ
    }
}
