package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
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
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class EditActionDialog(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_edit_dialog, OverlayLayer.PANEL, OverlayPriority.MEDIUM) {

    private var currentConfig: ActionConfig? = null

    override fun onViewInflated(view: View) {}

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            flags = WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
        }
    }

    fun show(config: ActionConfig) {
        currentConfig = config
        super.show()
        rootView?.let { bindUi(it, config) }
    }

    private fun bindUi(dialogView: View, config: ActionConfig) {
        val currentStepIdx = service.actionsList.indexOf(config)

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val etStepOrder = dialogView.findViewById<EditText>(R.id.etStepOrder)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etRepeat = dialogView.findViewById<EditText>(R.id.etRepeatCount)
        val etRadius = dialogView.findViewById<EditText>(R.id.etRandomRadius)
        val tvHoldTitle = dialogView.findViewById<TextView>(R.id.tvHoldTitle)
        val etHold = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val btnPrevStep = dialogView.findViewById<Button>(R.id.btnPrevStep)
        val btnNextStep = dialogView.findViewById<Button>(R.id.btnNextStep)
        val btnSaveHeader = dialogView.findViewById<View>(R.id.btnSaveHeader)
        val btnCloseHeader = dialogView.findViewById<View>(R.id.btnCloseHeader)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSave)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        val btnCloneAction = dialogView.findViewById<Button>(R.id.btnCloneAction)
        val btnDeleteAction = dialogView.findViewById<Button>(R.id.btnDeleteAction)

        val layoutAiBlock = dialogView.findViewById<View>(R.id.layoutAiParametersBlock)
        val etAiTimeout = dialogView.findViewById<EditText>(R.id.etAiTimeout)
        val etSimilarity = dialogView.findViewById<EditText>(R.id.etSimilarityPercent)
        val etScanInterval = dialogView.findViewById<EditText>(R.id.etScanInterval)
        val etPostMatchDelay = dialogView.findViewById<EditText>(R.id.etPostMatchDelay)
        val etJumpStep = dialogView.findViewById<EditText>(R.id.etJumpToStep)

        val btnCalibrate = dialogView.findViewById<Button>(R.id.btnCalibrateMatchesOnScreen)
        val btnToggleAiNotif = dialogView.findViewById<Button>(R.id.btnToggleAiNotification)
        val btnMultiTemplates = dialogView.findViewById<Button>(R.id.btnManageMultiTemplates)
        val btnClickTarget = dialogView.findViewById<Button>(R.id.btnToggleClickTarget)
        val btnScriptLoad = dialogView.findViewById<Button>(R.id.btnSelectScriptToLoad)

        val tvTemplateIndex = dialogView.findViewById<TextView>(R.id.tvTemplateIndex)
        val ivTemplatePreview = dialogView.findViewById<ImageView>(R.id.ivSelectedTemplateImagePreview)
        val btnPrevTemplate = dialogView.findViewById<Button>(R.id.btnPrevTemplate)
        val btnNextTemplate = dialogView.findViewById<Button>(R.id.btnNextTemplate)
        val btnDeleteSelectedTemplate = dialogView.findViewById<Button>(R.id.btnDeleteSelectedTemplate)

        tvTitle?.text = "Действие #${config.id}"
        etStepOrder?.setText(config.id.toString())
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeat?.setText(if (config.repeatCount == -1) "∞" else config.repeatCount.toString())
        etRadius?.setText(config.randomRadius.toString())
        etHold?.setText(config.holdDuration.toString())

        etAiTimeout?.setText(config.aiTimeoutSeconds.toString())
        etSimilarity?.setText(config.similarityPercent.toString())
        etScanInterval?.setText(config.scanIntervalSeconds.toString())
        etPostMatchDelay?.setText(config.postMatchDelaySeconds.toString())
        etJumpStep?.setText(if (config.jumpToStepOnMatch > 0) config.jumpToStepOnMatch.toString() else "0")

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
            val bmp = service.globalTemplates.getOrNull(idx) ?: BitmapFactory.decodeFile(maskPath)
            ivTemplatePreview?.setImageBitmap(bmp)
        }

        fun updateUi() {
            val isClick = selectedType == ActionType.CLICK
            val isHold = selectedType == ActionType.LONG_PRESS || selectedType == ActionType.HOLD
            val isSwipe = selectedType == ActionType.SWIPE || selectedType == ActionType.SWIPE_PATH
            val isTrigger = selectedType == ActionType.TRIGGER

            btnTypeClick?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isClick) R.color.accent_blue else R.color.panel_blue))
            btnTypeHold?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isHold) R.color.accent_blue else R.color.panel_blue))
            btnTypeSwipe?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isSwipe) R.color.accent_blue else R.color.panel_blue))
            btnTypeTrigger?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isTrigger) R.color.accent_blue else R.color.panel_blue))

            tvHoldTitle?.visibility = if (isHold) View.VISIBLE else View.GONE
            etHold?.visibility = if (isHold) View.VISIBLE else View.GONE

            layoutAiBlock?.visibility = if (isTrigger) View.VISIBLE else View.GONE

            btnToggleAiNotif?.text = if (config.playAudioOnMatch) "🔔 Звук / Вибро при совпадении: [ВКЛ]" else "🔔 Звук / Вибро при совпадении: [ВЫКЛ]"
            btnToggleAiNotif?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.playAudioOnMatch) R.color.accent_blue else R.color.panel_blue))

            val multiCount = config.multiTemplateIndices.size
            btnMultiTemplates?.text = if (multiCount > 0) "🗂 Мультишаблоны: [ Выбрано $multiCount маск ]" else "🗂 Мультишаблоны: [ Обычный режим (1 маска) ]"
            btnMultiTemplates?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (multiCount > 0) R.color.accent_blue else R.color.panel_blue))

            btnClickTarget?.text = if (config.clickAiTarget) "🎯 Клик по мишени: [ВКЛ]" else "🎯 Клик по мишени: [ВЫКЛ]"
            btnClickTarget?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.clickAiTarget) R.color.accent_blue else R.color.panel_blue))

            btnScriptLoad?.text = if (config.targetScriptToLoad.isNotEmpty()) "📁 Переход на сценарий: [ ${config.targetScriptToLoad} ]" else "📁 Переход на сценарий: [ НЕТ ]"
            btnScriptLoad?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.targetScriptToLoad.isNotEmpty()) R.color.accent_blue else R.color.panel_blue))

            if (isTrigger) updateTemplatePreviewUI()
        }

        btnTypeClick?.setOnClickListener { selectedType = ActionType.CLICK; updateUi() }
        btnTypeHold?.setOnClickListener { selectedType = ActionType.LONG_PRESS; updateUi() }
        btnTypeSwipe?.setOnClickListener { selectedType = ActionType.SWIPE; updateUi() }
        btnTypeTrigger?.setOnClickListener { selectedType = ActionType.TRIGGER; updateUi() }

        btnToggleAiNotif?.setOnClickListener { service.vibrateFeedback(20L); config.playAudioOnMatch = !config.playAudioOnMatch; updateUi() }
        btnClickTarget?.setOnClickListener { service.vibrateFeedback(20L); config.clickAiTarget = !config.clickAiTarget; updateUi() }
        btnScriptLoad?.setOnClickListener { service.vibrateFeedback(20L); service.showScriptPickerDialog("Выберите сценарий для перехода") { name -> config.targetScriptToLoad = name; updateUi() } }

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

        btnDeleteSelectedTemplate?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (config.selectedTemplateIndex in service.globalTemplatesNames.indices) {
                service.moveTemplateToTrash(config.selectedTemplateIndex)
                service.loadAllTemplatesFromDisk()
                updateTemplatePreviewUI()
                updateUi()
            }
        }

        fun saveCurrentData() {
            config.type = selectedType
            config.delay = ((etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0) * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHold?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L

            config.aiTimeoutSeconds = etAiTimeout?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 15
            config.similarityPercent = etSimilarity?.text?.toString()?.toIntOrNull()?.coerceIn(10, 99) ?: 70
            config.scanIntervalSeconds = etScanInterval?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 5
            config.postMatchDelaySeconds = etPostMatchDelay?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 3
            config.jumpToStepOnMatch = etJumpStep?.text?.toString()?.toIntOrNull() ?: -1

            ActionEditorEngine.validateAndNormalize(config)

            if (selectedType == ActionType.SWIPE && config.endView == null) {
                val screenSize = service.getRealScreenSize()
                val sw = screenSize.first
                val sh = screenSize.second
                service.spawnEndTargetAtPosition(config, sw / 2f + service.dpToPx(80), sh / 2f + service.dpToPx(80))
            } else if (selectedType != ActionType.SWIPE && config.endView != null) {
                service.overlayManager.safeRemoveView(config.endView)
                config.endView = null
            }
        }

        btnCalibrate?.setOnClickListener {
            service.vibrateFeedback(30L)
            saveCurrentData()
            hide()
            service.aiScannerEngine.startTemplateCalibration(config)
        }

        btnCloneAction?.setOnClickListener {
            service.vibrateFeedback(25L)
            saveCurrentData()
            hide()
            val screenSize = service.getRealScreenSize()
            val sw = screenSize.first
            val sh = screenSize.second
            service.addNewActionAtPosition(sw / 2f + service.dpToPx(20), sh / 2f + service.dpToPx(20), config.delay, config.type, config.selectedTemplateIndex)
            Toast.makeText(service, "📋 Шаг #${config.id} клонирован!", Toast.LENGTH_SHORT).show()
        }

        btnDeleteAction?.setOnClickListener {
            service.vibrateFeedback(30L)
            hide()
            service.overlayManager.safeRemoveView(config.startView)
            config.endView?.let { service.overlayManager.safeRemoveView(it) }
            service.actionsList.remove(config)
            for (i in service.actionsList.indices) {
                val act = service.actionsList[i]
                act.id = i + 1
                act.startView?.findViewById<TextView>(R.id.tvTargetNumber)?.text = act.id.toString()
                act.endView?.findViewById<TextView>(R.id.tvTargetNumberEnd)?.text = "${act.id}E"
            }
            Toast.makeText(service, "🗑 Шаг удален", Toast.LENGTH_SHORT).show()
        }

        btnPrevStep?.setOnClickListener {
            saveCurrentData()
            hide()
            if (currentStepIdx > 0) show(service.actionsList[currentStepIdx - 1])
        }

        btnNextStep?.setOnClickListener {
            saveCurrentData()
            hide()
            if (currentStepIdx < service.actionsList.size - 1) show(service.actionsList[currentStepIdx + 1])
        }

        val performSave = {
            service.vibrateFeedback(30L)
            saveCurrentData()
            hide()
            Toast.makeText(service, "Шаг #${config.id} сохранен!", Toast.LENGTH_SHORT).show()
        }

        val performClose = { service.vibrateFeedback(25L); hide() }

        btnSaveHeader?.setOnClickListener { performSave() }
        btnCloseHeader?.setOnClickListener { performClose() }
        btnSave?.setOnClickListener { performSave() }
        btnCancel?.setOnClickListener { performClose() }

        updateUi()
    }
}
