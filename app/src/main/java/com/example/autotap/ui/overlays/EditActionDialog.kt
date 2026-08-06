package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
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
    private var tvStepIndexView: TextView? = null

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

        tvStepIndexView = view.findViewByNames("tvTemplateIndex") as? TextView

        view.bindClickByNames("btnNextStep") {
            val listSize = MyAutoClickService.instance?.actionsList?.size ?: 0
            if (currentStepIdx < listSize - 1) {
                currentStepIdx++
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnPrevStep") {
            if (currentStepIdx > 0) {
                currentStepIdx--
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnDeleteAction") {
            val list = MyAutoClickService.instance?.actionsList
            if (list != null && list.isNotEmpty() && currentStepIdx in list.indices) {
                list.removeAt(currentStepIdx)
                context.vibrateFeedback()
                logDiagnostic("SCRIPT", "Шаг #$currentStepIdx удален из сценария.")
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
                logDiagnostic("SCRIPT", "Шаг #$currentStepIdx скопирован.")
                currentStepIdx++
                updateStepDisplay()
            }
        }

        view.bindClickByNames("btnSave", "btnSaveHeader") {
            logDiagnostic("SCRIPT", "Шаг сохранен в EditActionDialog.")
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
        val listSize = MyAutoClickService.instance?.actionsList?.size ?: 0
        tvStepIndexView?.text = "Шаг ${currentStepIdx + 1} из $listSize"
    }
}
