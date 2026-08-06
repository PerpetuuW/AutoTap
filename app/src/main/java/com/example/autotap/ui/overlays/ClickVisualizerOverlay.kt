package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.os.Handler
import android.os.Looper
import android.view.View
import com.example.autotap.dpToPx
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ClickVisualizerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val mainHandler = Handler(Looper.getMainLooper())

    override fun createView(): View {
        return View(context).apply {
            setBackgroundColor(Color.parseColor("#80FF0000"))
        }
    }

    fun showClickAt(x: Float, y: Float) {
        val size = 40.dpToPx(context)
        initialX = (x - size / 2).toInt()
        initialY = (y - size / 2).toInt()
        width = size
        height = size

        show()

        mainHandler.postDelayed({
            hide()
        }, 300L)
    }
}
