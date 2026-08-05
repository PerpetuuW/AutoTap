package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Point
import android.graphics.Rect
import com.example.autotap.*

data class MatchCandidate(
    val point: Point,
    val score: Float,
    val boundingBox: Rect
)

object HybridCascadeMatcher {

    /**
     * Real two-stage cascade matching:
     * 1) Coarse Stage: Fast spatial sampling over the search region calculating Mean Absolute Error (MAE).
     * 2) Fine Stage: Dense pixel-by-pixel local search around candidate regions for global score maximization.
     */
    fun match(
        frame: Bitmap,
        targetColor: Int,
        tolerance: Int,
        searchArea: Rect
    ): List<MatchCandidate> {
        val candidates = mutableListOf<MatchCandidate>()
        val startX = searchArea.left.coerceIn(0, frame.width - 1)
        val startY = searchArea.top.coerceIn(0, frame.height - 1)
        val endX = if (searchArea.right > 0) searchArea.right.coerceIn(startX, frame.width) else frame.width
        val endY = if (searchArea.bottom > 0) searchArea.bottom.coerceIn(startY, frame.height) else frame.height

        val targetR = Color.red(targetColor)
        val targetG = Color.green(targetColor)
        val targetB = Color.blue(targetColor)

        val coarseStep = 4

        // --- STAGE 1: COARSE SPATIAL SAMPLING ---
        for (y in startY until endY step coarseStep) {
            for (x in startX until endX step coarseStep) {
                val pixel = frame.getPixel(x, y)
                if (Color.alpha(pixel) < 30) continue

                val r = Color.red(pixel)
                val g = Color.green(pixel)
                val b = Color.blue(pixel)

                val diffR = Math.abs(r - targetR)
                val diffG = Math.abs(g - targetG)
                val diffB = Math.abs(b - targetB)

                if (diffR <= tolerance && diffG <= tolerance && diffB <= tolerance) {
                    val maxDiff = Math.max(diffR, Math.max(diffG, diffB)).toFloat()
                    val coarseScore = 1.0f - (maxDiff / 255.0f)
                    
                    // --- STAGE 2: FINE LOCAL REFINEMENT ---
                    val refinedCandidate = fineRefine(frame, targetR, targetG, targetB, tolerance, x, y)
                    candidates.add(refinedCandidate ?: MatchCandidate(Point(x, y), coarseScore, Rect(x - 10, y - 10, x + 10, y + 10)))
                }
            }
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun fineRefine(
        frame: Bitmap,
        targetR: Int,
        targetG: Int,
        targetB: Int,
        tolerance: Int,
        centerX: Int,
        centerY: Int
    ): MatchCandidate? {
        var bestPoint: Point? = null
        var bestScore = -1.0f

        val localRadius = 8
        val minX = (centerX - localRadius).coerceIn(0, frame.width - 1)
        val maxX = (centerX + localRadius).coerceIn(minX, frame.width - 1)
        val minY = (centerY - localRadius).coerceIn(0, frame.height - 1)
        val maxY = (centerY + localRadius).coerceIn(minY, frame.height - 1)

        for (y in minY..maxY) {
            for (x in minX..maxX) {
                val pixel = frame.getPixel(x, y)
                if (Color.alpha(pixel) < 30) continue

                val r = Color.red(pixel)
                val g = Color.green(pixel)
                val b = Color.blue(pixel)

                val diffR = Math.abs(r - targetR)
                val diffG = Math.abs(g - targetG)
                val diffB = Math.abs(b - targetB)

                if (diffR <= tolerance && diffG <= tolerance && diffB <= tolerance) {
                    val totalDiff = (diffR + diffG + diffB).toFloat()
                    val score = 1.0f - (totalDiff / (3.0f * 255.0f))
                    if (score > bestScore) {
                        bestScore = score
                        bestPoint = Point(x, y)
                    }
                }
            }
        }

        return bestPoint?.let {
            MatchCandidate(
                point = it,
                score = bestScore,
                boundingBox = Rect(it.x - 12, it.y - 12, it.x + 12, it.y + 12)
            )
        }
    }
}
