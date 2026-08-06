package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class SearchAreaOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_search_area_frame, null)

        view.bindClickByNames("btnSaveSearchArea") {
            logDiagnostic("AI_SCANNER", "Область поиска сохранена.")
            hide()
        }

        view.bindClickByNames("btnResetSearchArea", "btnCancelSearchArea") {
            hide()
        }

        val handle = view.findViewByNames("handleMoveSearchArea") ?: view
        setupDragAndDrop(handle)

        return view
    }
}
