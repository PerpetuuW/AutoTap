package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.PixelFormat
import android.os.Build
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

class EditActionDialog(private val service: MyAutoClickService) {

    fun show(config: ActionConfig) {
        val dialogView = LayoutInflater.from(service)
            .inflate(R.layout.floating_edit_dialog, null)

        val currentStepIdx = service.actionsList.indexOf(config)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        bindUi(dialogView, config, currentStepIdx)
        service.overlayManager.safeAddView(dialogView, params)
    }

    private fun bindUi(dialogView: View, config: ActionConfig, currentStepIdx: Int) {

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etRepeat = dialogView.findViewById<EditText>(R.id.etRepeatCount)
        val etRandomRadius = dialogView.findViewById<EditText>(R.id.etRandomRadius)
        val etHoldDuration = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val btnPrevStep = dialogView.findViewById<Button>(R.id.btnPrevStep)
        val btnNextStep = dialogView.findViewById<Button>(R.id.btnNextStep)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSave)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        tvTitle.text = "Действие #${config.id}"
        etDelay.setText((config.delay / 1000.0).toString())
        etRepeat.setText(config.repeatCount.toString())
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
            updateUi(dialogView, config, selectedType)
        }

        btnTypeHold.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.LONG_PRESS)
            updateUi(dialogView, config, selectedType)
        }

        btnTypeSwipe.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.SWIPE)
            updateUi(dialogView, config, selectedType)
        }

        btnTypeTrigger.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.TRIGGER)
            updateUi(dialogView, config, selectedType)
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
            service.overlayManager.safeRemoveView(dialogView)
            Toast.makeText(service, "Шаг #${config.id} сохранён", Toast.LENGTH_SHORT).show()
        }

        btnCancel.setOnClickListener {
            service.vibrateFeedback(20L)
            service.overlayManager.safeRemoveView(dialogView)
        }

        btnPrevStep.setOnClickListener {
            saveConfig()
            service.overlayManager.safeRemoveView(dialogView)
            if (currentStepIdx > 0) show(service.actionsList[currentStepIdx - 1])
        }

        btnNextStep.setOnClickListener {
            saveConfig()
            service.overlayManager.safeRemoveView(dialogView)
            if (currentStepIdx < service.actionsList.size - 1) show(service.actionsList[currentStepIdx + 1])
        }

        updateUi(dialogView, config, selectedType)
    }

    private fun updateUi(dialogView: View, config: ActionConfig, selectedType: ActionType) {

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val tvHoldTitle = dialogView.findViewById<TextView>(R.id.tvHoldTitle)
        val etHoldDuration = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val isClick = selectedType == ActionType.CLICK
        val isHold = selectedType == ActionType.LONG_PRESS
        val isSwipe = selectedType == ActionType.SWIPE
        val isTrigger = selectedType == ActionType.TRIGGER

        btnTypeClick.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isClick) R.color.accent_blue else R.color.panel_blue))

        btnTypeHold.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isHold) R.color.accent_blue else R.color.panel_blue))

        btnTypeSwipe.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isSwipe) R.color.accent_blue else R.color.panel_blue))

        btnTypeTrigger.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isTrigger) R.color.accent_blue else R.color.panel_blue))

        tvHoldTitle.visibility = if (isHold) View.VISIBLE else View.GONE
        etHoldDuration.visibility = if (isHold) View.VISIBLE else View.GONE
    }
}
