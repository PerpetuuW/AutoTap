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

class SaveRecordingDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var etScriptNameView: EditText? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_save_recording, null)

        etScriptNameView = view.findViewByNames("etRecordScriptName") as? EditText

        view.bindClickByNames("btnSaveRecordScript") {
            val name = etScriptNameView?.text?.toString()?.ifBlank { "recorded_script" } ?: "recorded_script"
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.recordingEngine.stopRecording(name)
                context.vibrateFeedback()
                logDiagnostic("SCRIPT", "Запись сохранена под именем '$name'")
            }
            hide()
        }

        view.bindClickByNames("btnSkipRecordScript") {
            hide()
        }

        return view
    }
}
