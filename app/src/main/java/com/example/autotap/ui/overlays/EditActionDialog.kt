package com.example.autotap.ui.overlays

import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class EditActionDialog(private val service: MyAutoClickService) {

    fun show(config: ActionConfig) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_edit_dialog, null)
        val params = service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            flags = WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
        }

        val tvTitle = view.findViewById<TextView>(R.id.tvDialogTitle)
        val etDelay = view.findViewById<EditText>(R.id.etDelay)
        val etRepeat = view.findViewById<EditText>(R.id.etRepeatCount)
        val etRadius = view.findViewById<EditText>(R.id.etRandomRadius)
        val etHold = view.findViewById<EditText>(R.id.etHoldDuration)
        val btnSave = view.findViewById<Button>(R.id.btnSave)
        val btnCancel = view.findViewById<Button>(R.id.btnCancel)

        tvTitle?.text = "Шаг #${config.id}"
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeat?.setText(config.repeatCount.toString())
        etRadius?.setText(config.randomRadius.toString())
        etHold?.setText(config.holdDuration.toString())

        btnSave?.setOnClickListener {
            service.vibrateFeedback(30L)
            config.delay = ((etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0) * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHold?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L
            service.overlayManager.safeRemoveView(view)
            Toast.makeText(service, "Шаг #${config.id} сохранен!", Toast.LENGTH_SHORT).show()
        }

        btnCancel?.setOnClickListener { service.vibrateFeedback(20L); service.overlayManager.safeRemoveView(view) }
        service.overlayManager.safeAddView(view, params)
    }
}
