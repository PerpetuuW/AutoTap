package com.example.autotap.ui.overlays

import android.view.Gravity
import android.view.LayoutInflater
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ScriptsDialog(private val service: MyAutoClickService) {

    fun show() {
        val view = LayoutInflater.from(service).inflate(R.layout.dialog_scripts, null)
        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val etName = view.findViewById<EditText>(R.id.etScriptName)
        val btnSave = view.findViewById<Button>(R.id.btnSaveScriptAction)
        val btnClose = view.findViewById<Button>(R.id.btnCloseScripts)

        btnSave?.setOnClickListener {
            val name = etName?.text?.toString()?.trim() ?: ""
            if (name.isNotEmpty()) {
                service.saveScriptByName(name, service.actionsList)
                etName?.setText("")
            }
        }

        btnClose?.setOnClickListener { service.overlayManager.safeRemoveView(view) }
        service.overlayManager.safeAddView(view, params)
    }
}
