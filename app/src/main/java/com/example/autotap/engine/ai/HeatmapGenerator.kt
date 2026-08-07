package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint

class HeatmapGenerator {

    fun generateHeatmap(frame: Bitmap, candidates: List<MatchCandidate>): Bitmap {
        val heatmap = Bitmap.createBitmap(frame.width, frame.height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(heatmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
        }

        for (c in candidates) {
            val score = c.score
            paint.color = when {
                score >= 0.85f -> Color.argb(140, 0, 245, 212)
                score >= 0.70f -> Color.argb(110, 255, 183, 3)
                else -> Color.argb(80, 240, 68, 56)
            }
            canvas.drawRect(c.boundingBox, paint)
        }
        return heatmap
    }
}
