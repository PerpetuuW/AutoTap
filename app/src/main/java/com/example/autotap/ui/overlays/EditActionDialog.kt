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

    private var etDelayView: EditText? = null
    private var etHoldDurationView: EditText? = null
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

        etDelayView = view.findViewByNames("etDelay") as? EditText
        etHoldDurationView = view.findViewByNames("etHoldDuration") as? EditText

        view.bindClickByNames("btnSave", "btnSaveHeader") {
            logDiagnostic("SCRIPT", "Шаг сохранен в floating_edit_dialog.")
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnCancel", "btnCloseHeader") {
            hide()
        }

        view.bindClickByNames("btnToggleClickTarget") { btn ->
            isClickTarget = !isClickTarget
            btn.isSelected = isClickTarget
            (btn as? Button)?.apply {
                text = if (isClickTarget) "Целевой клик: [ ВКЛ ]" else "Целевой клик: [ ВЫКЛ ]"
                setTextColor(if (isClickTarget) Color.parseColor("#00E676") else Color.WHITE)
            }
        }

        view.bindClickByNames("btnToggleAiNotification") { btn ->
            isAiNotification = !isAiNotification
            btn.isSelected = isAiNotification
            (btn as? Button)?.apply {
                text = if (isAiNotification) "Уведомление AI: [ ВКЛ ]" else "Уведомление AI: [ ВЫКЛ ]"
                setTextColor(if (isAiNotification) Color.parseColor("#00E676") else Color.WHITE)
            }
        }

        return view
    }
}
