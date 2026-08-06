package com.example.autotap.ui.overlays

import android.content.Context
import android.text.Editable
import android.text.TextWatcher
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.EditText
import android.widget.TextView
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

    private var tvSecClickDuration: TextView? = null
    private var tvSecSwipeDuration: TextView? = null
    private var tvSecPreScreenshot: TextView? = null

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

        tvSecClickDuration = view.findViewByNames("tvSecClickDuration") as? TextView
        tvSecSwipeDuration = view.findViewByNames("tvSecSwipeDuration") as? TextView
        tvSecPreScreenshot = view.findViewByNames("tvSecPreScreenshot") as? TextView

        setupLiveSecondCalculation()

        view.bindClickByNames("btnSaveGlobalSettings") {
            val clickMs = etClickDuration?.text?.toString()?.toLongOrNull() ?: 120L
            val swipeMs = etSwipeDuration?.text?.toString()?.toLongOrNull() ?: 300L
            val preScreenshotMs = etPreScreenshot?.text?.toString()?.toLongOrNull() ?: 250L

            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.globalClickDurationMs = clickMs
                svc.globalSwipeDurationMs = swipeMs
                svc.globalPreScreenshotDelayMs = preScreenshotMs
                logDiagnostic("UI", "Сохранены все глобальные настройки: click=$clickMs ms, swipe=$swipeMs ms, preScreenshot=$preScreenshotMs ms")
            }
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnCancelGlobalSettings") {
            hide()
        }

        return view
    }

    private fun setupLiveSecondCalculation() {
        val svc = MyAutoClickService.instance
        if (svc != null) {
            etClickDuration?.setText(svc.globalClickDurationMs.toString())
            etSwipeDuration?.setText(svc.globalSwipeDurationMs.toString())
            etPreScreenshot?.setText(svc.globalPreScreenshotDelayMs.toString())
        }

        updateLabels()

        val textWatcher = object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                updateLabels()
            }
            override fun afterTextChanged(s: Editable?) {}
        }

        etClickDuration?.addTextChangedListener(textWatcher)
        etSwipeDuration?.addTextChangedListener(textWatcher)
        etPreScreenshot?.addTextChangedListener(textWatcher)
    }

    private fun updateLabels() {
        val clickMs = etClickDuration?.text?.toString()?.toLongOrNull() ?: 0L
        val swipeMs = etSwipeDuration?.text?.toString()?.toLongOrNull() ?: 0L
        val preScreenshotMs = etPreScreenshot?.text?.toString()?.toLongOrNull() ?: 0L

        tvSecClickDuration?.text = "= ${"%.2f".format(clickMs / 1000f)} сек"
        tvSecSwipeDuration?.text = "= ${"%.2f".format(swipeMs / 1000f)} сек"
        tvSecPreScreenshot?.text = "= ${"%.2f".format(preScreenshotMs / 1000f)} сек"
    }
}
