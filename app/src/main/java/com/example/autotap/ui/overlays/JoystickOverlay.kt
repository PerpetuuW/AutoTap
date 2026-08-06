package com.example.autotap.ui.overlays

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class JoystickOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        layer = OverlayLayer.JOYSTICK_LAYER
        priority = OverlayPriority.MEDIUM
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = try {
            inflater.inflate(R.layout.floating_joystick_control, null)
        } catch (e: Exception) {
            View(context)
        }

        setupDragAndDrop(view)
        return view
    }

    fun performSwipeAction(startX: Float, startY: Float, endX: Float, endY: Float, durationMs: Long) {
        val service = MyAutoClickService.instance ?: return
        service.gestureExecutor.performSwipeWithCallback(startX, startY, endX, endY, durationMs) { success: Boolean ->
            logDiagnostic("OVERLAY", "Результат свайпа джойстика: $success")
        }
    }
}
