package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class AddActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_add_action, null)

        view.bindClickByNames("btnAddClick") {
            MyAutoClickService.instance?.addNewActionAtPosition(0.5f, 0.5f)
            logDiagnostic("SCRIPT", "Добавлено действие КЛИК.")
            hide()
        }

        view.bindClickByNames("btnAddTrigger", "btnAddAi", "btnAddSwipe") {
            logDiagnostic("OVERLAY", "Открытие прицела захвата маски из AddActionDialog.")
            overlayManager.captureFrameOverlay.show()
            hide()
        }

        view.bindClickByNames("btnCancelAdd") {
            hide()
        }

        return view
    }
}
