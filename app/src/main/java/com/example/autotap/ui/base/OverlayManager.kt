package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import java.util.concurrent.ConcurrentHashMap

class OverlayManager(private val context: Context) {

    private val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    private val attachedViews = ConcurrentHashMap<View, Boolean>()
    private val viewPool = ConcurrentHashMap<Int, MutableList<View>>()
    private val activeOverlays = ConcurrentHashMap<OverlayLayer, MutableList<OverlayBase>>()

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] == true) return
        try {
            windowManager.addView(view, params)
            attachedViews[view] = true
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun safeRemoveView(view: View?) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        } finally {
            attachedViews.remove(view)
        }
    }

    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.updateViewLayout(view, params)
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun getViewFromReusePool(layoutResId: Int): View? {
        val pool = viewPool[layoutResId]
        return if (!pool.isNullOrEmpty()) pool.removeAt(0) else null
    }

    fun recycleViewToPool(layoutResId: Int, view: View) {
        val pool = viewPool.getOrPut(layoutResId) { mutableListOf() }
        if (pool.size < 5 && !pool.contains(view)) {
            pool.add(view)
        }
    }

    fun pushOverlay(overlay: OverlayBase) {
        val list = activeOverlays.getOrPut(overlay.layer) { mutableListOf() }
        list.add(overlay)
        overlay.show()
    }

    fun popOverlay(layer: OverlayLayer) {
        val list = activeOverlays[layer]
        if (!list.isNullOrEmpty()) {
            val overlay = list.removeAt(list.size - 1)
            overlay.hide()
        }
    }

    fun clearLayer(layer: OverlayLayer) {
        activeOverlays[layer]?.forEach { it.hide() }
        activeOverlays[layer]?.clear()
    }

    fun detachOnStop() {
        clearLayer(OverlayLayer.DEBUG)
        clearLayer(OverlayLayer.CAPTURE)
        clearLayer(OverlayLayer.JOYSTICK)
        clearLayer(OverlayLayer.CANDIDATE)
        clearLayer(OverlayLayer.VISUALIZER)
    }

    fun detachOnScriptChange() {
        detachOnStop()
    }

    fun detachOnError() {
        detachOnStop()
    }

    fun detachOnOrientationChange() {
        activeOverlays.values.forEach { list ->
            list.forEach { if (it.isShowing) { it.hide(); it.show() } }
        }
    }

    fun dpToPx(dp: Int): Int = (dp * context.resources.displayMetrics.density).toInt()
    fun dpToPx(dp: Float): Int = (dp * context.resources.displayMetrics.density).toInt()

    fun getRealScreenSize(): Pair<Int, Int> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val bounds = windowManager.currentWindowMetrics.bounds
            Pair(bounds.width(), bounds.height())
        } else {
            val dm = DisplayMetrics()
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay.getRealMetrics(dm)
            Pair(dm.widthPixels, dm.heightPixels)
        }
    }

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

            gravity = Gravity.TOP or Gravity.START

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }

            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }
    }
}
