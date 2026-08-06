package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.vibrateFeedback

class EditActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        width = 800
        height = 600
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    override fun createView(): View {
        return LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            setPadding(32, 32, 32, 32)

            addView(TextView(context).apply {
                text = "Редактирование шага"
                setTextColor(Color.BLACK)
                textSize = 18f
                setPadding(0, 0, 0, 16)
            })

            addView(Button(context).apply {
                text = "Калибровка маски"
                setOnClickListener {
                    val svc = MyAutoClickService.instance
                    if (svc != null) {
                        val calibrated = svc.templateRepository.recalibrateTemplate(0)
                        if (calibrated != null) {
                            context.vibrateFeedback()
                            logDiagnostic("AI_SCANNER", "Ручная калибровка завершена: контур ${calibrated.contour.size} точек, BBox: ${calibrated.boundingBox}")
                        } else {
                            logDiagnostic("AI_SCANNER", "Калибровка не выполнена: шаблон #0 не найден.")
                        }
                    }
                }
            })

            addView(Button(context).apply {
                text = "Сохранить шаг"
                setOnClickListener {
                    logDiagnostic("SCRIPT", "Шаг сохранен в EditActionDialog")
                    context.vibrateFeedback()
                    hide()
                }
            })
        }
    }
}
