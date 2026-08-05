package com.example.autotap.ui.overlays

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ClickVisualizerOverlay(private val service: MyAutoClickService) {

    fun showClickAt(x: Float, y: Float) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_beacon_ring, null)
        val sizePx = service.dpToPx(40)
        val params = service.overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            this.x = (x - sizePx / 2f).toInt()
            this.y = (y - sizePx / 2f).toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.alpha = 0f
        view.scaleX = 0.4f
        view.scaleY = 0.4f

        val fadeIn = ObjectAnimator.ofFloat(view, View.ALPHA, 0f, 1f).setDuration(80)
        val scaleX = ObjectAnimator.ofFloat(view, View.SCALE_X, 0.4f, 1.8f).setDuration(280)
        val scaleY = ObjectAnimator.ofFloat(view, View.SCALE_Y, 0.4f, 1.8f).setDuration(280)
        val fadeOut = ObjectAnimator.ofFloat(view, View.ALPHA, 1f, 0f).setDuration(150)
        fadeOut.startDelay = 150

        AnimatorSet().apply {
            playTogether(fadeIn, scaleX, scaleY, fadeOut)
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: android.animation.Animator) {
                    service.overlayManager.safeRemoveView(view)
                }
            })
            start()
        }
    }
}
