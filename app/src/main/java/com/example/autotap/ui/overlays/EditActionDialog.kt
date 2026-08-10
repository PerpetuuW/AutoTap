package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.playNotificationAlert
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class EditActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.floating_edit_dialog

    private var targetStepIndex: Int = -1
    private var etEditX: EditText? = null
    private var etEditY: EditText? = null
    private var etEditDelayMs: EditText? = null
    private var etEditSimilarity: EditText? = null
    private var etEditAiTimeout: EditText? = null
    private var btnToggleNotificationMode: Button? = null
    private var cbLoopUntilStopped: CheckBox? = null
    private var tvSelectedTemplatesSummary: TextView? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    fun setTargetStepIndex(index: Int) {
        this.targetStepIndex = index
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        etEditX = view.findViewByNames("etEditX") as? EditText
        etEditY = view.findViewByNames("etEditY") as? EditText
        etEditDelayMs = view.findViewByNames("etEditDelayMs") as? EditText
        etEditSimilarity = view.findViewByNames("etEditSimilarity") as? EditText
        etEditAiTimeout = view.findViewByNames("etEditAiTimeout") as? EditText
        btnToggleNotificationMode = view.findViewByNames("btnToggleNotificationMode") as? Button
        cbLoopUntilStopped = view.findViewByNames("cbLoopUntilStopped") as? CheckBox
        tvSelectedTemplatesSummary = view.findViewByNames("tvSelectedTemplatesSummary") as? TextView

        val actions = MyAutoClickService.instance?.actionsList ?: emptyList()
        val stepAction = if (targetStepIndex in actions.indices) {
            actions[targetStepIndex]
        } else actions.lastOrNull()

        if (stepAction != null) {
            bindActionToUI(stepAction)
        }

        view.bindClickByNames("btnOpenTemplatePicker") {
            val currentList = if (stepAction?.multiTemplateIndices?.isNotEmpty() == true) {
                stepAction.multiTemplateIndices
            } else listOf(stepAction?.selectedTemplateIndex ?: 0)

            overlayManager.templatePickerDialog.showPicker(currentList) { selected ->
                if (selected.isNotEmpty() && stepAction != null) {
                    stepAction.multiTemplateIndices = selected
                    stepAction.selectedTemplateIndex = selected[0]
                    updateSummaryText(selected)
                }
            }
        }

        view.bindClickByNames("btnToggleNotificationMode") {
            val action = stepAction ?: return@bindClickByNames
            action.notificationMode = (action.notificationMode + 1) % 4
            updateNotificationButtonText(action.notificationMode)
            context.playNotificationAlert(action.notificationMode)
        }

        view.bindClickByNames("btnEditApply", "btnSave") {
            val action = stepAction
            val screenSize = context.getRealScreenSize()
            if (action != null) {
                val inputX = etEditX?.text?.toString()?.toFloatOrNull()
                val inputY = etEditY?.text?.toString()?.toFloatOrNull()

                if (inputX != null) {
                    action.xNorm = if (inputX > 1.0f) (inputX / screenSize.x).coerceIn(0f, 1f) else inputX.coerceIn(0f, 1f)
                }
                if (inputY != null) {
                    action.yNorm = if (inputY > 1.0f) (inputY / screenSize.y).coerceIn(0f, 1f) else inputY.coerceIn(0f, 1f)
                }

                action.delay = etEditDelayMs?.text?.toString()?.toLongOrNull() ?: action.delay
                action.similarityPercent = etEditSimilarity?.text?.toString()?.toIntOrNull()?.coerceIn(10, 100) ?: action.similarityPercent
                action.aiTimeoutSeconds = etEditAiTimeout?.text?.toString()?.toFloatOrNull()?.coerceAtLeast(0.1f) ?: action.aiTimeoutSeconds
                action.loopUntilStopped = cbLoopUntilStopped?.isChecked ?: action.loopUntilStopped
            }
            logDiagnostic("SCRIPT", "Изменения сохранены: X=${action?.xNorm}, Y=${action?.yNorm}, Timeout=${action?.aiTimeoutSeconds}s")
            hide()
        }

        view.bindClickByNames("btnEditDelete", "btnDeleteAction") {
            val list = MyAutoClickService.instance?.actionsList
            if (list != null && list.isNotEmpty()) {
                val removeIdx = if (targetStepIndex in list.indices) targetStepIndex else list.size - 1
                list.removeAt(removeIdx)
            }
            hide()
        }

        view.bindClickByNames("btnEditClose", "btnCancel") {
            hide()
        }

        return view
    }

    private fun bindActionToUI(action: ActionConfig) {
        val screenSize = context.getRealScreenSize()
        etEditX?.setText((action.xNorm * screenSize.x).toInt().toString())
        etEditY?.setText((action.yNorm * screenSize.y).toInt().toString())

        etEditDelayMs?.setText(action.delay.toString())
        etEditSimilarity?.setText(action.similarityPercent.toString())
        etEditAiTimeout?.setText(action.aiTimeoutSeconds.toString())
        cbLoopUntilStopped?.isChecked = action.loopUntilStopped
        updateNotificationButtonText(action.notificationMode)

        val list = if (action.multiTemplateIndices.isNotEmpty()) action.multiTemplateIndices else listOf(action.selectedTemplateIndex)
        updateSummaryText(list)
    }

    private fun updateSummaryText(indices: List<Int>) {
        tvSelectedTemplatesSummary?.text = "Выбранные маски (${indices.size}): #" + indices.joinToString(", #")
    }

    private fun updateNotificationButtonText(mode: Int) {
        val label = when (mode) {
            1 -> "🔔 Оповещение: [ 📳 ВИБРО ]"
            2 -> "🔔 Оповещение: [ 🔊 ЗВУК ]"
            3 -> "🔔 Оповещение: [ 🔊+📳 ЗВУК + ВИБРО ]"
            else -> "🔔 Оповещение: [ ВЫКЛ ]"
        }
        btnToggleNotificationMode?.text = label
    }
}
