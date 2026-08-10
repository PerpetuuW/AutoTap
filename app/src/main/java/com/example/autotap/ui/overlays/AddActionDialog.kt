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
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
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
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.addNewActionAtPosition(0.5f, 0.5f)
                overlayManager.updateTargetMarkers()
            }
            hide()
        }

        view.bindClickByNames("btnAddSwipe") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.actionsList.add(ActionConfig(type = ActionType.SWIPE, xNorm = 0.3f, yNorm = 0.5f, endXNorm = 0.7f, endYNorm = 0.5f))
                overlayManager.updateTargetMarkers()
            }
            hide()
        }

        view.bindClickByNames("btnAddTrigger", "btnAddAi") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                val action = ActionConfig(
                    type = ActionType.AI_SEARCH,
                    selectedTemplateIndex = 0,
                    similarityPercent = 85,
                    loopUntilStopped = true
                )
                svc.actionsList.add(action)
                overlayManager.updateTargetMarkers()
                overlayManager.editActionDialog.setTargetStepIndex(svc.actionsList.size - 1)
                overlayManager.editActionDialog.show()
            }
            hide()
        }

        view.bindClickByNames("btnCancelAdd") {
            hide()
        }

        return view
    }
}
