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
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class GlobalSettingsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var etClickDuration: EditText? = null
    private var etSwipeDuration: EditText? = null
    private var etPreScreenshot: EditText? = null

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

        etClickDuration = view.findViewByNames("etGlobalClickDuration") as? EditText
        etSwipeDuration = view.findViewByNames("etGlobalSwipeDuration") as? EditText
        etPreScreenshot = view.findViewByNames("etGlobalPreScreenshot") as? EditText

        view.bindClickByNames("btnSaveGlobalSettings") {
            val clickMs = etClickDuration?.text?.toString()?.toLongOrNull() ?: 50L
            MyAutoClickService.instance?.globalClickDurationMs = clickMs
            logDiagnostic("UI", "Глобальные настройки сохранены: clickDuration=$clickMs")
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnCancelGlobalSettings") {
            hide()
        }

        return view
    }
}
