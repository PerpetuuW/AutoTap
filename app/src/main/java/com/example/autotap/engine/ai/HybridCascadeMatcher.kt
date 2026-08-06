package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.PointF
import android.graphics.Rect
import kotlin.math.abs

class HybridCascadeMatcher {

    fun match(
        frame: Bitmap,
        mask: Bitmap,
        searchArea: Rect,
        modes: SearchModes,
        threshold: Float
    ): List<MatchCandidate> {
        val candidates = mutableListOf<MatchCandidate>()
        val step = if (modes.hybridCascadeMode) 4 else 1

        val startX = searchArea.left
        val startY = searchArea.top
        val endX = (searchArea.right - mask.width).coerceAtLeast(startX)
        val endY = (searchArea.bottom - mask.height).coerceAtLeast(startY)

        if (endX <= startX || endY <= startY) return candidates

        var x = startX
        while (x <= endX) {
            var y = startY
            while (y <= endY) {
                val score = comparePatch(frame, mask, x, y)
                if (score >= threshold) {
                    val pt = PointF(x + mask.width / 2f, y + mask.height / 2f)
                    val bbox = Rect(x, y, x + mask.width, y + mask.height)
                    candidates.add(MatchCandidate(pt, score, bbox, 1.0f, 0))
                }
                y += step
            }
            x += step
        }
        return candidates
    }

    private fun comparePatch(frame: Bitmap, mask: Bitmap, x: Int, y: Int): Float {
        var totalDiff = 0L
        var pixelCount = 0

        val stepX = (mask.width / 16).coerceAtLeast(1)
        val stepY = (mask.height / 16).coerceAtLeast(1)

        var mx = 0
        while (mx < mask.width) {
            var my = 0
            while (my < mask.height) {
                val framePixel = frame.getPixel(x + mx, y + my)
                val maskPixel = mask.getPixel(mx, my)

                val fr = (framePixel shr 16) and 0xFF
                val fg = (framePixel shr 8) and 0xFF
                val fb = framePixel and 0xFF

                val mr = (maskPixel shr 16) and 0xFF
                val mg = (maskPixel shr 8) and 0xFF
                val mb = maskPixel and 0xFF

                totalDiff += abs(fr - mr) + abs(fg - mg) + abs(fb - mb)
                pixelCount++

                my += stepY
            }
            mx += stepX
        }

        if (pixelCount == 0) return 0f
        val maxDiff = pixelCount * 255f * 3f
        val similarity = 1.0f - (totalDiff.toFloat() / maxDiff)
        return similarity.coerceIn(0f, 1f)
    }
}
