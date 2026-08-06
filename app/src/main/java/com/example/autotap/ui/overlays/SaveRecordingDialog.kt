package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.data.ScriptMetadata
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class SaveRecordingDialog(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_save_recording

    private var onSavedCallback: ((String) -> Unit)? = null
    private var onCloseCallback: (() -> Unit)? = null

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
        bind(view)
        return view
    }

    fun openForSaving(
        onSaved: ((String) -> Unit)? = null,
        onClose: (() -> Unit)? = null
    ) {
        this.onSavedCallback = onSaved
        this.onCloseCallback = onClose
        show()
        val v = rootView ?: return
        bind(v)
    }

    private fun bind(v: View) {
        val etName = v.findViewById<EditText>(R.id.etSaveScriptName)
        val etLoop = v.findViewById<EditText>(R.id.etSaveLoopCount)
        val cbInfinite = v.findViewById<CheckBox>(R.id.cbSaveInfinite)
        val btnSave = v.findViewById<Button>(R.id.btnSaveRecording)
        val btnClose = v.findViewById<Button>(R.id.btnSaveClose)

        btnSave?.setOnClickListener {
            val name = etName?.text?.toString()?.trim()?.ifBlank {
                "script_${SimpleDateFormat("MMdd_HHmm", Locale.US).format(Date())}"
            } ?: "script_${System.currentTimeMillis() % 10000}"

            val loopCount = etLoop?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            val isInfinite = cbInfinite?.isChecked ?: false

            val svc = MyAutoClickService.instance
            if (svc != null) {
                val metadata = ScriptMetadata(
                    name = name,
                    stepCount = svc.actionsList.size,
                    loopCount = loopCount,
                    isInfinite = isInfinite
                )
                svc.scriptRepository.saveScript(name, svc.actionsList, metadata)
                context.vibrateFeedback()
                logDiagnostic("SCRIPT", "Запись '$name' успешно сохранена из SaveRecordingDialog (loopCount=$loopCount, infinite=$isInfinite)")
                onSavedCallback?.invoke(name)
            }
            hide()
        }

        btnClose?.setOnClickListener {
            hide()
            onCloseCallback?.invoke()
        }
    }
}
