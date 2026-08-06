package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
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
        return LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#CC111111"))
            setPadding(24, 24, 24, 24)

            addView(Button(context).apply {
                text = "Захватить область экрана (0.5, 0.5)"
                setOnClickListener {
                    logDiagnostic("OVERLAY", "Захват области экрана выполнен.")
                    context.vibrateFeedback()
                    MyAutoClickService.instance?.addNewActionAtPosition(0.5f, 0.5f)
                    hide()
                }
            })

            addView(Button(context).apply {
                text = "Закрыть"
                setOnClickListener {
                    hide()
                }
            })
        }
    }
}
