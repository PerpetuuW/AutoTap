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
import android.widget.LinearLayout
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
    private var btnToggleNotificationMode: Button? = null
    private var cbLoopUntilStopped: CheckBox? = null
    private var templatesPickerContainer: LinearLayout? = null
    private val selectedMaskIndices = mutableSetOf<Int>()

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
        btnToggleNotificationMode = view.findViewByNames("btnToggleNotificationMode") as? Button
        cbLoopUntilStopped = view.findViewByNames("cbLoopUntilStopped") as? CheckBox
        templatesPickerContainer = view.findViewByNames("layoutTemplatesPickerContainer") as? LinearLayout

        val actions = MyAutoClickService.instance?.actionsList ?: emptyList()
        val stepAction = if (targetStepIndex in actions.indices) {
            actions[targetStepIndex]
        } else actions.lastOrNull()

        if (stepAction != null) {
            bindActionToUI(stepAction)
        }

        view.bindClickByNames("btnSelectAllTemplates") {
            selectAllTemplates(true)
        }

        view.bindClickByNames("btnUnselectAllTemplates") {
            selectAllTemplates(false)
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

                // Сохранение выбранных масок для мультипоиска
                val sortedList = selectedMaskIndices.sorted()
                if (sortedList.isNotEmpty()) {
                    action.multiTemplateIndices = sortedList
                    action.selectedTemplateIndex = sortedList[0]
                }

                action.loopUntilStopped = cbLoopUntilStopped?.isChecked ?: action.loopUntilStopped
            }
            logDiagnostic("SCRIPT", "Изменения сохранены: MultiTemplates=${action?.multiTemplateIndices}")
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
        cbLoopUntilStopped?.isChecked = action.loopUntilStopped
        updateNotificationButtonText(action.notificationMode)

        selectedMaskIndices.clear()
        if (action.multiTemplateIndices.isNotEmpty()) {
            selectedMaskIndices.addAll(action.multiTemplateIndices)
        } else {
            selectedMaskIndices.add(action.selectedTemplateIndex)
        }

        populateTemplatesPickerList()
    }

    private fun populateTemplatesPickerList() {
        val container = templatesPickerContainer ?: return
        container.removeAllViews()

        val templateFiles = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") }
            ?.sortedBy { file ->
                file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: 0
            } ?: emptyList()

        if (templateFiles.isEmpty()) {
            val emptyTv = TextView(context).apply {
                text = "ИИ-масок пока нет. Вырежьте их прицелом 📷"
                setTextColor(Color.GRAY)
                setPadding(12, 12, 12, 12)
            }
            container.addView(emptyTv)
            return
        }

        for (file in templateFiles) {
            val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
            val row = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(8, 6, 8, 6)
            }

            val cb = CheckBox(context).apply {
                isChecked = selectedMaskIndices.contains(index)
                setOnCheckedChangeListener { _, isChecked ->
                    if (isChecked) selectedMaskIndices.add(index) else selectedMaskIndices.remove(index)
                }
            }

            val iv = ImageView(context).apply {
                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                if (bitmap != null) setImageBitmap(bitmap)
                layoutParams = LinearLayout.LayoutParams(40, 40).apply { setMargins(8, 0, 12, 0) }
            }

            val tv = TextView(context).apply {
                text = "Маска #$index (${file.length() / 1024} КБ)"
                setTextColor(Color.WHITE)
                textSize = 12f
            }

            row.addView(cb)
            row.addView(iv)
            row.addView(tv)
            container.addView(row)
        }
    }

    private fun selectAllTemplates(select: Boolean) {
        val container = templatesPickerContainer ?: return
        selectedMaskIndices.clear()

        val templateFiles = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") } ?: emptyArray()
        if (select) {
            for (file in templateFiles) {
                val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
                selectedMaskIndices.add(index)
            }
        }

        for (i in 0 until container.childCount) {
            val row = container.getChildAt(i) as? LinearLayout ?: continue
            val cb = row.getChildAt(0) as? CheckBox ?: continue
            cb.isChecked = select
        }
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
