package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
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

class EditActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var currentStepIdx = 0
    private var tvDialogTitleView: TextView? = null
    private var tvStepIndexView: TextView? = null
    private var tvSelectTemplateTitleView: TextView? = null
    private var tvAiTimeoutTitleView: TextView? = null
    private var tvHoldTitleView: TextView? = null

    private var etDelayView: EditText? = null
    private var etHoldDurationView: EditText? = null
    private var etRepeatCountView: EditText? = null
    private var etScanIntervalView: EditText? = null
    private var etSimilarityPercentView: EditText? = null
    private var etRandomRadiusView: EditText? = null
    private var etJumpToStepView: EditText? = null
    private var etPostMatchDelayView: EditText? = null
    private var etAiTimeoutView: EditText? = null
    private var etStepOrderView: EditText? = null

    private var ivPreviewView: ImageView? = null

    private var layoutAiParametersBlockView: View? = null
    private var layoutAiTimeoutBlockView: View? = null
    private var layoutTemplateSelectorView: View? = null
    private var scrollViewEditView: View? = null

    private var isClickTarget = false
    private var isAiNotification = true

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
        val view = inflater.inflate(R.layout.floating_edit_dialog, null)

        tvDialogTitleView = view.findViewByNames("tvDialogTitle") as? TextView
        tvStepIndexView = view.findViewByNames("tvTemplateIndex") as? TextView
        tvSelectTemplateTitleView = view.findViewByNames("tvSelectTemplateTitle") as? TextView
        tvAiTimeoutTitleView = view.findViewByNames("tvAiTimeoutTitle") as? TextView
        tvHoldTitleView = view.findViewByNames("tvHoldTitle") as? TextView

        etDelayView = view.findViewByNames("etDelay") as? EditText
        etHoldDurationView = view.findViewByNames("etHoldDuration") as? EditText
        etRepeatCountView = view.findViewByNames("etRepeatCount") as? EditText
        etScanIntervalView = view.findViewByNames("etScanInterval") as? EditText
        etSimilarityPercentView = view.findViewByNames("etSimilarityPercent") as? EditText
        etRandomRadiusView = view.findViewByNames("etRandomRadius") as? EditText
        etJumpToStepView = view.findViewByNames("etJumpToStep") as? EditText
        etPostMatchDelayView = view.findViewByNames("etPostMatchDelay") as? EditText
        etAiTimeoutView = view.findViewByNames("etAiTimeout") as? EditText
        etStepOrderView = view.findViewByNames("etStepOrder") as? EditText

        ivPreviewView = view.findViewByNames("ivSelectedTemplateImagePreview") as? ImageView

        layoutAiParametersBlockView = view.findViewByNames("layoutAiParametersBlock")
        layoutAiTimeoutBlockView = view.findViewByNames("layoutAiTimeoutBlock")
        layoutTemplateSelectorView = view.findViewByNames("layoutTemplateSelector")
        scrollViewEditView = view.findViewByNames("scrollViewEdit")

        view.bindClickByNames("btnTypeClick") {
            logDiagnostic("SCRIPT", "Режим редактирования: Клик")
        }
        view.bindClickByNames("btnTypeHold") {
            logDiagnostic("SCRIPT", "Режим редактирования: Зажатие")
        }
        view.bindClickByNames("btnTypeSwipe") {
            logDiagnostic("SCRIPT", "Режим редактирования: Свайп")
        }
        view.bindClickByNames("btnTypeTrigger") {
            logDiagnostic("SCRIPT", "Режим редактирования: ИИ-Триггер")
        }

        view.bindClickByNames("btnSelectScriptToLoad") {
            overlayManager.scriptsDialog.show()
        }

        view.bindClickByNames("btnManageMultiTemplates") {
            overlayManager.templatesManagerDialog.show()
        }

        view.bindClickByNames("btnCalibrateMatchesOnScreen") {
            val svc = MyAutoClickService.instance
            svc?.templateRepository?.recalibrateTemplate(0)
            context.vibrateFeedback()
        }

        view.bindClickByNames("btnNextStep", "btnNextTemplate") {
            val listSize = MyAutoClickService.instance?.actionsList?.size ?: 0
            if (currentStepIdx < listSize - 1) {
                currentStepIdx++
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnPrevStep", "btnPrevTemplate") {
            if (currentStepIdx > 0) {
                currentStepIdx--
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnDeleteSelectedTemplate", "btnDeleteAction") {
            val list = MyAutoClickService.instance?.actionsList
            if (list != null && list.isNotEmpty() && currentStepIdx in list.indices) {
                list.removeAt(currentStepIdx)
                context.vibrateFeedback()
                if (currentStepIdx >= list.size) {
                    currentStepIdx = (list.size - 1).coerceAtLeast(0)
                }
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnCloneAction") {
            val list = MyAutoClickService.instance?.actionsList
            if (list != null && list.isNotEmpty() && currentStepIdx in list.indices) {
                val cloned = list[currentStepIdx].copy()
                list.add(currentStepIdx + 1, cloned)
                context.vibrateFeedback()
                currentStepIdx++
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnToggleClickTarget") { btn ->
            isClickTarget = !isClickTarget
            btn.isSelected = isClickTarget
            (btn as? Button)?.text = if (isClickTarget) "Целевой клик: [ ВКЛ ]" else "Целевой клик: [ ВЫКЛ ]"
        }

        view.bindClickByNames("btnToggleAiNotification") { btn ->
            isAiNotification = !isAiNotification
            btn.isSelected = isAiNotification
            (btn as? Button)?.text = if (isAiNotification) "Уведомление AI: [ ВКЛ ]" else "Уведомление AI: [ ВЫКЛ ]"
        }

        view.bindClickByNames("btnSave", "btnSaveHeader") {
            saveCurrentStepConfig()
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnCancel", "btnCloseHeader") {
            hide()
        }

        updateStepDisplay()
        return view
    }

    private fun updateStepDisplay() {
        val list = MyAutoClickService.instance?.actionsList ?: return
        if (currentStepIdx in list.indices) {
            val action = list[currentStepIdx]
            tvDialogTitleView?.text = "Редактирование шага #${currentStepIdx + 1}"
            tvStepIndexView?.text = "Шаг ${currentStepIdx + 1} из ${list.size} (${action.type.name})"
            etDelayView?.setText((action.delay / 1000f).toString())
            etHoldDurationView?.setText(action.holdDuration.toString())
            etSimilarityPercentView?.setText(action.similarityPercent.toString())
            etRandomRadiusView?.setText(action.randomRadius.toInt().toString())
            etScanIntervalView?.setText(action.scanIntervalSeconds.toInt().toString())
            etStepOrderView?.setText((currentStepIdx + 1).toString())
        } else {
            tvDialogTitleView?.text = "Сценарий пуст"
            tvStepIndexView?.text = "Шаблон: Нет"
        }
    }

    private fun saveCurrentStepConfig() {
        val list = MyAutoClickService.instance?.actionsList ?: return
        if (currentStepIdx in list.indices) {
            val action = list[currentStepIdx]
            val delaySec = etDelayView?.text?.toString()?.toFloatOrNull() ?: 1.0f
            action.delay = (delaySec * 1000L).toLong()
            action.holdDuration = etHoldDurationView?.text?.toString()?.toLongOrNull() ?: 100L
            action.similarityPercent = etSimilarityPercentView?.text?.toString()?.toIntOrNull() ?: 70
            action.randomRadius = etRandomRadiusView?.text?.toString()?.toFloatOrNull() ?: 0f
            logDiagnostic("SCRIPT", "Настройки шага #${currentStepIdx + 1} сохранены из floating_edit_dialog")
        }
    }
}
