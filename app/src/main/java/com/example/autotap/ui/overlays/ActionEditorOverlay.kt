package com.example.autotap.ui.overlays

import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class ActionEditorOverlay(
    private val service: MyAutoClickService,
    private val overlayManager: OverlayManager
) {

    private var editorView: View? = null
    private var currentConfig: ActionConfig? = null
    private var currentIndex: Int = -1

    fun show(config: ActionConfig) {
        hide()

        currentConfig = config
        currentIndex = service.actionsList.indexOf(config)

        val view = LayoutInflater.from(service).inflate(R.layout.floating_edit_dialog, null)
        editorView = view

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }

        bindUi(view, config)
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        editorView?.let { overlayManager.safeRemoveView(it) }
        editorView = null
        currentConfig = null
        currentIndex = -1
    }

    private fun bindUi(view: View, config: ActionConfig) {
        val tvTitle = view.findViewById<TextView>(R.id.tvDialogTitle)
        val etDelay = view.findViewById<EditText>(R.id.etDelay)
        val etRepeat = view.findViewById<EditText>(R.id.etRepeatCount)
        val etRandomRadius = view.findViewById<EditText>(R.id.etRandomRadius)
        val etHoldDuration = view.findViewById<EditText>(R.id.etHoldDuration)

        val btnTypeClick = view.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = view.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = view.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = view.findViewById<Button>(R.id.btnTypeTrigger)

        val btnPrev = view.findViewById<Button>(R.id.btnPrevStep)
        val btnNext = view.findViewById<Button>(R.id.btnNextStep)
        val btnSave = view.findViewById<Button>(R.id.btnSave)
        val btnCancel = view.findViewById<Button>(R.id.btnCancel)

        tvTitle.text = "Шаг #${config.id}"
        etDelay.setText((config.delay / 1000.0).toString())
        etRepeat.setText(if (config.repeatCount == -1) "∞" else config.repeatCount.toString())
        etRandomRadius.setText(config.randomRadius.toString())
        etHoldDuration.setText(config.holdDuration.toString())

        var selectedType = config.type

        fun applyType(t: ActionType) {
            selectedType = t
            config.type = t
        }

        btnTypeClick.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.CLICK)
        }

        btnTypeHold.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.LONG_PRESS)
        }

        btnTypeSwipe.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.SWIPE)
        }

        btnTypeTrigger.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.TRIGGER)
        }

        fun saveConfig() {
            val delaySec = etDelay.text.toString().toDoubleOrNull() ?: 1.0
            config.delay = (delaySec * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat.text.toString().toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRandomRadius.text.toString().toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHoldDuration.text.toString().toLongOrNull()?.coerceAtLeast(100L) ?: 1000L
        }

        btnSave.setOnClickListener {
            service.vibrateFeedback(30L)
            saveConfig()
            hide()
            Toast.makeText(service, "Шаг #${config.id} сохранён", Toast.LENGTH_SHORT).show()
        }

        btnCancel.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        btnPrev.setOnClickListener {
            saveConfig()
            if (currentIndex > 0) {
                hide()
                show(service.actionsList[currentIndex - 1])
            }
        }

        btnNext.setOnClickListener {
            saveConfig()
            if (currentIndex < service.actionsList.size - 1) {
                hide()
                show(service.actionsList[currentIndex + 1])
            }
        }
    }
}
