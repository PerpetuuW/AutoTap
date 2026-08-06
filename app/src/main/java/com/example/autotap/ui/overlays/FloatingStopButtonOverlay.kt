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

class FloatingStopButtonOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.TOP or Gravity.END
        initialX = 20
        initialY = 200
        layer = OverlayLayer.PANEL_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_stop_button, null)

        view.bindClickByNames("btnFloatingStop") {
            logDiagnostic("OVERLAY", "Нажата кнопка btnFloatingStop")
            MyAutoClickService.instance?.scriptExecutor?.stop()
            hide()
        }

        setupDragAndDrop(view)
        return view
    }
}
