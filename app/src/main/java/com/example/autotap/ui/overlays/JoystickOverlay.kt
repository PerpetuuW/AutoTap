package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class JoystickOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var joystickBaseView: View? = null
    private var joystickKnobView: View? = null
    private var joystickContainerView: View? = null

    init {
        width = 180.dpToPx(context)
        height = 220.dpToPx(context)
        gravity = Gravity.BOTTOM or Gravity.START
        initialX = 50
        initialY = 100
        layer = OverlayLayer.JOYSTICK_LAYER
        priority = OverlayPriority.MEDIUM
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_joystick_control, null)

        joystickBaseView = view.findViewByNames("viewJoystickBase")
        joystickKnobView = view.findViewByNames("viewJoystickKnob")
        joystickContainerView = view.findViewByNames("layoutJoystickContainer")

        view.bindClickByNames("btnCloseJoystick") {
            hide()
        }

        view.bindClickByNames("btnRecordJoystick") {
            logDiagnostic("JOYSTICK", "Нажата btnRecordJoystick")
            MyAutoClickService.instance?.recordingEngine?.startJoystickRecording()
        }

        val handle = view.findViewByNames("handleMoveJoystick") ?: view
        setupDragAndDrop(handle)

        return view
    }
}
