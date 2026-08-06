package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_capture_frame, null)

        view.bindClickByNames("btn_capture_confirm", "btnCaptureConfirm", "btn_capture", "btn_confirm") {
            logDiagnostic("OVERLAY", "Захват области экрана выполнен.")
            context.vibrateFeedback()
            MyAutoClickService.instance?.addNewActionAtPosition(0.5f, 0.5f)
            hide()
        }

        view.bindClickByNames("btn_close_capture", "btnCloseCapture", "btn_close", "btnClose") {
            hide()
        }

        return view
    }
}
