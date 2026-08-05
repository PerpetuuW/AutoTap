package com.example.autotap.ui.base

import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService

abstract class OverlayBase(
    protected val service: MyAutoClickService,
    protected val layoutResId: Int
) {
    var rootView: View? = null
        protected set

    val isShowing: Boolean
        get() = rootView != null && rootView?.parent != null

    open fun show() {
        if (isShowing) return
        val view = LayoutInflater.from(service).inflate(layoutResId, null)
        rootView = view
        val params = createParams()
        onViewInflated(view)
        service.overlayManager.safeAddView(view, params)
    }

    open fun hide() {
        rootView?.let { service.overlayManager.safeRemoveView(it) }
        rootView = null
    }

    protected open fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams()
    }

    protected abstract fun onViewInflated(view: View)

    protected fun <T : View> findViewById(id: Int): T? {
        return rootView?.findViewById(id)
    }
}
