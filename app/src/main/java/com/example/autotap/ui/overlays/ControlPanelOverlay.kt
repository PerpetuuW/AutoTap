package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val container = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#DD1E1E2C"))
            setPadding(24, 24, 24, 24)
        }

        val titleText = TextView(context).apply {
            text = "AutoTap v35 Control"
            setTextColor(Color.WHITE)
            textSize = 16f
            setPadding(0, 0, 0, 16)
        }
        container.addView(titleText)

        val btnStart = Button(context).apply {
            text = "СТАРТ"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка СТАРТ нажата.")
                MyAutoClickService.instance?.scriptExecutor?.start()
            }
        }
        container.addView(btnStart)

        val btnAddAction = Button(context).apply {
            text = "+ ДЕЙСТВИЕ"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка +ДЕЙСТВИЕ нажата.")
                overlayManager.captureFrameOverlay.show()
            }
        }
        container.addView(btnAddAction)

        val btnScripts = Button(context).apply {
            text = "СЦЕНАРИИ"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка СЦЕНАРИИ нажата.")
                overlayManager.scriptsDialog.show()
            }
        }
        container.addView(btnScripts)

        val btnHelp = Button(context).apply {
            text = "СПРАВКА"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Открытие справки InfoHelpDialog.")
                overlayManager.infoHelpDialog.show()
            }
        }
        container.addView(btnHelp)

        val btnStop = Button(context).apply {
            text = "СТОП"
            setOnClickListener {
                logDiagnostic("OVERLAY", "Кнопка СТОП нажата.")
                MyAutoClickService.instance?.scriptExecutor?.stop()
                hide()
            }
        }
        container.addView(btnStop)

        setupDragAndDrop(container)
        return container
    }
}
