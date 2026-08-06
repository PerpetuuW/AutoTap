package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Color

class HeatmapGenerator {

    fun generate(frame: Bitmap, mask: Bitmap): Bitmap {
        val width = frame.width
        val height = frame.height
        val heatmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)

        for (x in 0 until width step 8) {
            for (y in 0 until height step 8) {
                val score = 0.5f
                val color = colorize(score)
                for (dx in 0 until 8) {
                    for (dy in 0 until 8) {
                        if (x + dx < width && y + dy < height) {
                            heatmap.setPixel(x + dx, y + dy, color)
                        }
                    }
                }
            }
        }
        return heatmap
    }

    private fun colorize(score: Float): Int {
        return when {
            score > 0.85f -> Color.argb(150, 255, 0, 0)
            score > 0.65f -> Color.argb(120, 255, 165, 0)
            score > 0.45f -> Color.argb(90, 255, 255, 0)
            else -> Color.argb(40, 0, 0, 255)
        }
    }
}
