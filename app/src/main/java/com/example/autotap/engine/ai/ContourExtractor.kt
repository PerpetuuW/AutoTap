package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.PointF

class ContourExtractor {

    fun extract(mask: Bitmap): List<PointF> {
        val points = mutableListOf<PointF>()
        val width = mask.width
        val height = mask.height
        if (width <= 2 || height <= 2) return points

        val step = (width / 20).coerceAtLeast(1)
        for (x in 0 until width step step) {
            for (y in 0 until height step step) {
                val pixel = mask.getPixel(x, y)
                val alpha = (pixel shr 24) and 0xFF
                if (alpha > 128) {
                    points.add(PointF(x.toFloat(), y.toFloat()))
                }
            }
        }
        return simplifyContour(points)
    }

    private fun simplifyContour(points: List<PointF>): List<PointF> {
        if (points.size <= 50) return points
        val step = points.size / 50
        return points.filterIndexed { index, _ -> index % step == 0 }
    }
}
