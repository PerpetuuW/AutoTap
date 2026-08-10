package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.CheckBox
import android.widget.EditText
import android.widget.Toast
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.data.ScriptMetadata
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class SaveRecordingDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_save_recording

    private var etSaveScriptName: EditText? = null
    private var etSaveLoopCount: EditText? = null
    private var cbSaveInfinite: CheckBox? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        etSaveScriptName = view.findViewByNames("etSaveScriptName") as? EditText
        etSaveLoopCount = view.findViewByNames("etSaveLoopCount") as? EditText
        cbSaveInfinite = view.findViewByNames("cbSaveInfinite") as? CheckBox

        view.bindClickByNames("btnSaveRecording", "btnSaveRecordScript") {
            val name = etSaveScriptName?.text?.toString()?.takeIf { it.isNotBlank() } ?: "recording_1"
            val loops = etSaveLoopCount?.text?.toString()?.toIntOrNull() ?: 1
            val isInfinite = cbSaveInfinite?.isChecked ?: false

            val svc = MyAutoClickService.instance
            if (svc != null) {
                val metadata = ScriptMetadata(
                    name = name,
                    stepCount = svc.recordingEngine.recordedActions.size,
                    loopCount = loops,
                    isInfinite = isInfinite
                )
                svc.recordingEngine.stopRecording(name)
                svc.scriptRepository.saveScript(name, svc.actionsList, metadata)
                logDiagnostic("RECORDING", "Запись сохранена с именем '$name' ($loops повторов, бесконечно: $isInfinite)")
                Toast.makeText(context, "Запись '$name' сохранена!", Toast.LENGTH_SHORT).show()
                overlayManager.updateTargetMarkers()
            }
            hide()
        }

        view.bindClickByNames("btnSaveClose", "btnSkipRecordScript") {
            hide()
        }

        return view
    }
}
