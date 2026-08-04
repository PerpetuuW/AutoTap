package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import java.util.concurrent.ConcurrentHashMap

class OverlayManager(private val context: Context) {

    private val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    private val attachedViews = ConcurrentHashMap<View, Boolean>()
    private val updateHandler = Handler(Looper.getMainLooper())
    private val pendingUpdates = ConcurrentHashMap<View, WindowManager.LayoutParams>()

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null) return
        if (attachedViews[view] == true) return

        try {
            windowManager.addView(view, params)
            attachedViews[view] = true
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun safeRemoveView(view: View?) {
        if (view == null) return
        if (attachedViews[view] != true) return

        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        } finally {
            attachedViews.remove(view)
        }
    }

    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null) return
        if (attachedViews[view] != true) return

        pendingUpdates[view] = params

        updateHandler.removeCallbacksAndMessages(null)
        updateHandler.postDelayed({
            try {
                val p = pendingUpdates[view] ?: return@postDelayed
                windowManager.updateViewLayout(view, p)
            } catch (e: Exception) {
                MyAutoClickService.logError(context, e)
            } finally {
                pendingUpdates.remove(view)
            }
        }, 8)
    }

    fun dpToPx(dp: Int): Int =
        (dp * context.resources.displayMetrics.density).toInt()

    fun dpToPx(dp: Float): Int =
        (dp * context.resources.displayMetrics.density).toInt()

    fun getOverlayType(): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
    }

    fun createOverlayParams(): WindowManager.LayoutParams {
        return WindowManager.LayoutParams().apply {
            type = getOverlayType()
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN

            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }
    }
}
