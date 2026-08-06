package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.vibrateFeedback

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
    }

    override fun createView(): View {
        return LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#CC111111"))
            setPadding(24, 24, 24, 24)

            addView(Button(context).apply {
                text = "Захватить центр экрана (0.5, 0.5)"
                setOnClickListener {
                    logDiagnostic("OVERLAY", "Захват точки по нажатию в CaptureFrameOverlay")
                    context.vibrateFeedback()
                    MyAutoClickService.instance?.addNewActionAtPosition(0.5f, 0.5f)
                    hide()
                }
            })

            addView(Button(context).apply {
                text = "Калибровка маски #0"
                setOnClickListener {
                    val svc = MyAutoClickService.instance
                    if (svc != null) {
                        val calibrated = svc.templateRepository.recalibrateTemplate(0)
                        if (calibrated != null) {
                            context.vibrateFeedback()
                            logDiagnostic("AI_SCANNER", "Ручная калибровка в CaptureFrameOverlay выполнена!")
                        }
                    }
                }
            })
        }
    }
}
