package com.example.autotap.util

import android.content.Context
import android.graphics.Point
import android.graphics.PointF
import com.example.autotap.*

object ScreenCalibrator {

    fun normalizeCoordinates(context: Context, x: Int, y: Int): PointF {
        val screenSize = context.getRealScreenSize()
        val rx = if (screenSize.x > 0) x.toFloat() / screenSize.x.toFloat() else 0f
        val ry = if (screenSize.y > 0) y.toFloat() / screenSize.y.toFloat() else 0f
        return PointF(rx, ry)
    }

    fun denormalizeCoordinates(context: Context, rx: Float, ry: Float): Point {
        val screenSize = context.getRealScreenSize()
        val x = (rx * screenSize.x).toInt()
        val y = (ry * screenSize.y).toInt()
        return Point(x, y)
    }
}
