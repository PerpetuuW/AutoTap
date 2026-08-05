package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class EditActionDialog(private val service: MyAutoClickService) {

    fun show(config: ActionConfig) {
        val dialogView = LayoutInflater.from(service).inflate(R.layout.floating_edit_dialog, null)
        val currentStepIdx = service.actionsList.indexOf(config)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val btnPrevStep = dialogView.findViewById<Button>(R.id.btnPrevStep)
        val btnNextStep = dialogView.findViewById<Button>(R.id.btnNextStep)

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val etStepOrder = dialogView.findViewById<EditText>(R.id.etStepOrder)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etRepeatCount = dialogView.findViewById<EditText>(R.id.etRepeatCount)
        val etRandomRadius = dialogView.findViewById<EditText>(R.id.etRandomRadius)
        val tvHoldTitle = dialogView.findViewById<TextView>(R.id.tvHoldTitle)
        val etHoldDuration = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val tvTemplateIndex = dialogView.findViewById<TextView>(R.id.tvTemplateIndex)
        val ivTemplatePreview = dialogView.findViewById<ImageView>(R.id.ivSelectedTemplateImagePreview)
        val btnPrevTemplate = dialogView.findViewById<Button>(R.id.btnPrevTemplate)
        val btnNextTemplate = dialogView.findViewById<Button>(R.id.btnNextTemplate)

        val btnCloneAction = dialogView.findViewById<Button>(R.id.btnCloneAction)
        val btnDeleteAction = dialogView.findViewById<Button>(R.id.btnDeleteAction)
        val btnSaveHeader = dialogView.findViewById<View>(R.id.btnSaveHeader)
        val btnCloseHeader = dialogView.findViewById<View>(R.id.btnCloseHeader)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSave)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        tvTitle?.text = "Действие #${config.id}"
        etStepOrder?.setText(config.id.toString())
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeatCount?.setText(if (config.repeatCount == -1) "∞" else config.repeatCount.toString())
        etRandomRadius?.setText(config.randomRadius.toString())
        etHoldDuration?.setText(config.holdDuration.toString())

        var selectedType = config.type

        fun updateTemplatePreviewUI() {
            if (service.globalTemplatesNames.isEmpty()) {
                tvTemplateIndex?.text = "Шаблонов нет (0)"
                ivTemplatePreview?.setImageBitmap(null)
                config.selectedTemplateIndex = -1
                return
            }

            if (config.selectedTemplateIndex !in service.globalTemplatesNames.indices) {
                config.selectedTemplateIndex = 0
            }

            val idx = config.selectedTemplateIndex
            val total = service.globalTemplatesNames.size
            val maskPath = service.globalTemplatesNames[idx]
            val fileName = File(maskPath).nameWithoutExtension

            tvTemplateIndex?.text = "№${idx + 1}/$total: $fileName"
            ivTemplatePreview?.setBackgroundColor(Color.parseColor("#3A4763"))
            val bmp = service.globalTemplates.getOrNull(idx) ?: android.graphics.BitmapFactory.decodeFile(maskPath)
            ivTemplatePreview?.setImageBitmap(bmp)
        }

        fun updateUI() {
            val isClick = selectedType == ActionType.CLICK
            val isHold = selectedType == ActionType.LONG_PRESS
            val isSwipe = selectedType == ActionType.SWIPE
            val isTrigger = selectedType == ActionType.TRIGGER

            btnTypeClick?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isClick) R.color.accent_blue else R.color.panel_blue))
            btnTypeHold?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isHold) R.color.accent_blue else R.color.panel_blue))
            btnTypeSwipe?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isSwipe) R.color.accent_blue else R.color.panel_blue))
            btnTypeTrigger?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isTrigger) R.color.accent_blue else R.color.panel_blue))

            tvHoldTitle?.visibility = if (isHold) View.VISIBLE else View.GONE
            etHoldDuration?.visibility = if (isHold) View.VISIBLE else View.GONE

            val layoutAiBlock = dialogView.findViewById<View>(R.id.layoutAiParametersBlock)
            layoutAiBlock?.visibility = if (isTrigger) View.VISIBLE else View.GONE

            val etAiTimeout = dialogView.findViewById<EditText>(R.id.etAiTimeout)
            etAiTimeout?.setText(config.aiTimeoutSeconds.toString())

            val etSimPct = dialogView.findViewById<EditText>(R.id.etSimilarityPercent)
            etSimPct?.setText(config.similarityPercent.toString())

            val etInterval = dialogView.findViewById<EditText>(R.id.etScanInterval)
            etInterval?.setText(config.scanIntervalSeconds.toString())

            val etPostDelay = dialogView.findViewById<EditText>(R.id.etPostMatchDelay)
            etPostDelay?.setText(config.postMatchDelaySeconds.toString())

            val etJumpStep = dialogView.findViewById<EditText>(R.id.etJumpToStep)
            etJumpStep?.setText(config.jumpToStepOnMatch.toString())

            val btnAiNotif = dialogView.findViewById<Button>(R.id.btnToggleAiNotification)
            btnAiNotif?.text = if (config.playAudioOnMatch) "🔔 Звук / Вибро при совпадении: [ВКЛ]" else "🔔 Звук / Вибро при совпадении: [ВЫКЛ]"
            btnAiNotif?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.playAudioOnMatch) R.color.accent_blue else R.color.panel_blue))

            val btnMulti = dialogView.findViewById<Button>(R.id.btnManageMultiTemplates)
            val multiCount = config.multiTemplateIndices.size
            btnMulti?.text = if (multiCount > 0) "🗂 Мультишаблоны: [ Выбрано $multiCount маск ]" else "🗂 Мультишаблоны: [ Обычный режим (1 маска) ]"

            val btnClickTarget = dialogView.findViewById<Button>(R.id.btnToggleClickTarget)
            btnClickTarget?.text = if (config.clickAiTarget) "🎯 Клик по мишени: [ВКЛ]" else "🎯 Клик по мишени: [ВЫКЛ]"

            val btnScriptLoad = dialogView.findViewById<Button>(R.id.btnSelectScriptToLoad)
            btnScriptLoad?.text = if (config.targetScriptToLoad.isNotEmpty()) "📁 Переход на сценарий: [ ${config.targetScriptToLoad} ]" else "📁 Переход на сценарий: [ НЕТ ]"

            if (isTrigger) {
                updateTemplatePreviewUI()
            }
        }

        val btnAiNotif = dialogView.findViewById<Button>(R.id.btnToggleAiNotification)
        btnAiNotif?.setOnClickListener {
            service.vibrateFeedback(20L)
            config.playAudioOnMatch = !config.playAudioOnMatch
            updateUI()
        }

        val btnScriptLoad = dialogView.findViewById<Button>(R.id.btnSelectScriptToLoad)
        btnScriptLoad?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showScriptPickerDialog("Выберите сценарий для перехода") { name ->
                config.targetScriptToLoad = name
                updateUI()
            }
        }

        val btnDelTemplate = dialogView.findViewById<Button>(R.id.btnDeleteSelectedTemplate)
        btnDelTemplate?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (config.selectedTemplateIndex in service.globalTemplatesNames.indices) {
                service.moveTemplateToTrash(config.selectedTemplateIndex)
                service.loadAllTemplatesFromDisk()
                updateTemplatePreviewUI()
                updateUI()
            }
        }

        val btnCalibrate = dialogView.findViewById<Button>(R.id.btnCalibrateMatchesOnScreen)
        btnCalibrate?.setOnClickListener {
            service.vibrateFeedback(30L)
            service.overlayManager.safeRemoveView(dialogView)
            service.startTemplateCalibration(config)
        }

        val btnClickTarget = dialogView.findViewById<Button>(R.id.btnToggleClickTarget)
        btnClickTarget?.setOnClickListener {
            service.vibrateFeedback(20L)
            config.clickAiTarget = !config.clickAiTarget
            updateUI()
        }

        btnPrevTemplate?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.globalTemplatesNames.isNotEmpty()) {
                config.selectedTemplateIndex = (config.selectedTemplateIndex - 1 + service.globalTemplatesNames.size) % service.globalTemplatesNames.size
                updateTemplatePreviewUI()
            }
        }

        btnNextTemplate?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.globalTemplatesNames.isNotEmpty()) {
                config.selectedTemplateIndex = (config.selectedTemplateIndex + 1) % service.globalTemplatesNames.size
                updateTemplatePreviewUI()
            }
        }

        btnTypeClick?.setOnClickListener { selectedType = ActionType.CLICK; updateUI() }
        btnTypeHold?.setOnClickListener { selectedType = ActionType.LONG_PRESS; updateUI() }
        btnTypeSwipe?.setOnClickListener { selectedType = ActionType.SWIPE; updateUI() }
        btnTypeTrigger?.setOnClickListener { selectedType = ActionType.TRIGGER; updateUI() }

        fun saveCurrentStepData() {
            config.type = selectedType
            val delaySec = etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0
            config.delay = (delaySec * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeatCount?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRandomRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHoldDuration?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L

            val etAiTimeout = dialogView.findViewById<EditText>(R.id.etAiTimeout)
            config.aiTimeoutSeconds = etAiTimeout?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 15

            val etSimPct = dialogView.findViewById<EditText>(R.id.etSimilarityPercent)
            config.similarityPercent = etSimPct?.text?.toString()?.toIntOrNull()?.coerceIn(10, 99) ?: 70

            val etInterval = dialogView.findViewById<EditText>(R.id.etScanInterval)
            config.scanIntervalSeconds = etInterval?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 5

            val etPostDelay = dialogView.findViewById<EditText>(R.id.etPostMatchDelay)
            config.postMatchDelaySeconds = etPostDelay?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 3

            val etJumpStep = dialogView.findViewById<EditText>(R.id.etJumpToStep)
            config.jumpToStepOnMatch = etJumpStep?.text?.toString()?.toIntOrNull() ?: -1

            if (selectedType == ActionType.SWIPE && config.endView == null) {
                val loc = IntArray(2)
                config.startView.getLocationOnScreen(loc)
                service.spawnEndTargetAtPosition(config, loc[0].toFloat() + service.overlayManager.dpToPx(80), loc[1].toFloat() + service.overlayManager.dpToPx(80))
            } else if (selectedType != ActionType.SWIPE && config.endView != null) {
                service.overlayManager.safeRemoveView(config.endView)
                config.endView = null
            }
        }

        btnCloneAction?.setOnClickListener {
            service.vibrateFeedback(25L)
            saveCurrentStepData()
            service.overlayManager.safeRemoveView(dialogView)

            val loc = IntArray(2)
            config.startView.getLocationOnScreen(loc)
            service.addNewActionAtPosition(loc[0].toFloat() + service.overlayManager.dpToPx(20), loc[1].toFloat() + service.overlayManager.dpToPx(20), config.delay, config.type, config.selectedTemplateIndex)
            Toast.makeText(service, "📋 Шаг #${config.id} успешно клонирован!", Toast.LENGTH_SHORT).show()
        }

        btnDeleteAction?.setOnClickListener {
            service.vibrateFeedback(30L)
            service.overlayManager.safeRemoveView(dialogView)
            service.overlayManager.safeRemoveView(config.startView)
            config.endView?.let { service.overlayManager.safeRemoveView(it) }
            service.actionsList.remove(config)

            for (i in service.actionsList.indices) {
                val act = service.actionsList[i]
                act.id = i + 1
                act.startView.findViewById<TextView>(R.id.tvTargetNumber)?.text = act.id.toString()
                act.endView?.findViewById<TextView>(R.id.tvTargetNumberEnd)?.text = "${act.id}E"
            }
            Toast.makeText(service, "🗑 Шаг удален", Toast.LENGTH_SHORT).show()
        }

        btnPrevStep?.setOnClickListener {
            saveCurrentStepData()
            service.overlayManager.safeRemoveView(dialogView)
            if (currentStepIdx > 0) show(service.actionsList[currentStepIdx - 1])
        }

        btnNextStep?.setOnClickListener {
            saveCurrentStepData()
            service.overlayManager.safeRemoveView(dialogView)
            if (currentStepIdx < service.actionsList.size - 1) show(service.actionsList[currentStepIdx + 1])
        }

        val performSave = {
            service.vibrateFeedback(30L)
            saveCurrentStepData()
            service.overlayManager.safeRemoveView(dialogView)
            Toast.makeText(service, "Параметры шага #${config.id} сохранены!", Toast.LENGTH_SHORT).show()
        }

        btnSaveHeader?.setOnClickListener { performSave() }
        btnCloseHeader?.setOnClickListener { service.overlayManager.safeRemoveView(dialogView) }
        btnSave?.setOnClickListener { performSave() }
        btnCancel?.setOnClickListener { service.overlayManager.safeRemoveView(dialogView) }

        updateUI()
        service.overlayManager.safeAddView(dialogView, params)
    }
}
