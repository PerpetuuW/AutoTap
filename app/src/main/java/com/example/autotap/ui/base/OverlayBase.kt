package com.example.autotap.ui.base

import com.example.autotap.*

import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService

abstract class OverlayBase(
    protected val service: MyAutoClickService,
    val layoutResId: Int = 0,
    val layer: OverlayLayer = OverlayLayer.PANEL,
    val priority: OverlayPriority = OverlayPriority.MEDIUM
) {
    var rootView: View? = null
        protected set

    val isShowing: Boolean
        get() = rootView != null && rootView?.parent != null

    open fun onAttach() {}
    open fun onDetach() {}
    open fun onUpdate() {}
    open fun onVisibilityChanged(visible: Boolean) {}

    open fun show() {
        if (isShowing) {
            rootView?.visibility = View.VISIBLE
            onVisibilityChanged(true)
            return
        }

        val view = if (layoutResId != 0) {
            service.overlayManager.getViewFromReusePool(layoutResId)
                ?: LayoutInflater.from(service).inflate(layoutResId, null)
        } else {
            rootView
        }

        if (view == null) return

        rootView = view
        val params = createParams()
        onViewInflated(view)
        service.overlayManager.safeAddView(view, params)
        onAttach()
        fadeIn()
    }

    open fun hide() {
        if (!isShowing) return
        fadeOut {
            rootView?.let {
                service.overlayManager.safeRemoveView(it)
                if (layoutResId != 0) {
                    service.overlayManager.recycleViewToPool(layoutResId, it)
                }
            }
            onDetach()
            rootView = null
        }
    }

    protected open fun fadeIn(duration: Long = 180L) {
        rootView?.let { v ->
            v.alpha = 0f
            v.animate().alpha(1f).setDuration(duration).start()
        }
    }

    protected open fun fadeOut(onEnd: () -> Unit) {
        rootView?.let { v ->
            v.animate().alpha(0f).setDuration(150L).withEndAction { onEnd() }.start()
        } ?: onEnd()
    }

    protected open fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams()
    }

    protected abstract fun onViewInflated(view: View)

    protected fun <T : View> findViewById(id: Int): T? {
        return rootView?.findViewById(id)
    }
}
