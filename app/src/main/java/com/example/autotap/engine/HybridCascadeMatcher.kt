package com.example.autotap.engine

import com.example.autotap.*

import android.graphics.Bitmap
import android.graphics.PointF
import android.graphics.Rect
import com.example.autotap.MatchCandidate

object HybridCascadeMatcher {

    fun match(
        frame: Bitmap,
        calibratedMask: CalibratedMask,
        searchArea: Rect?,
        modes: SearchModes
    ): List<MatchCandidate> {

        val coarseCandidates = coarseMatch(
            frameDownscaled = calibratedMask.downscaledFrame,
            maskDownscaled = calibratedMask.downscaledMask,
            searchArea = searchArea
        )

        val fineCandidates = coarseCandidates.mapNotNull { coarse ->
            fineMatch(
                fullFrame = frame,
                fullMask = calibratedMask.originalMask,
                coarseRect = coarse.rect
            )
        }

        return rankCandidates(fineCandidates, modes)
    }

    private fun coarseMatch(
        frameDownscaled: Bitmap,
        maskDownscaled: Bitmap,
        searchArea: Rect?
    ): List<MatchCandidate> {

        val results = mutableListOf<MatchCandidate>()
        val w = (frameDownscaled.width - maskDownscaled.width).coerceAtLeast(1)
        val h = (frameDownscaled.height - maskDownscaled.height).coerceAtLeast(1)

        val area = searchArea ?: Rect(0, 0, w, h)

        for (y in area.top until area.bottom.coerceAtMost(h) step 2) {
            for (x in area.left until area.right.coerceAtMost(w) step 2) {

                val score = fastCompare(frameDownscaled, maskDownscaled, x, y)
                if (score > 0.55f) {
                    results.add(
                        MatchCandidate(
                            rect = Rect(x, y, x + maskDownscaled.width, y + maskDownscaled.height),
                            score = score
                        )
                    )
                }
            }
        }

        return results
    }

    private fun fineMatch(
        fullFrame: Bitmap,
        fullMask: Bitmap,
        coarseRect: Rect
    ): MatchCandidate? {

        val w = fullMask.width
        val h = fullMask.height

        val startX = (coarseRect.left * 2).coerceIn(0, (fullFrame.width - w).coerceAtLeast(0))
        val startY = (coarseRect.top * 2).coerceIn(0, (fullFrame.height - h).coerceAtLeast(0))

        var bestScore = 0f
        var bestX = -1
        var bestY = -1

        for (y in startY until (startY + 10).coerceAtMost(fullFrame.height - h + 1)) {
            for (x in startX until (startX + 10).coerceAtMost(fullFrame.width - w + 1)) {

                val score = preciseCompare(fullFrame, fullMask, x, y)
                if (score > bestScore) {
                    bestScore = score
                    bestX = x
                    bestY = y
                }
            }
        }

        if (bestX == -1) return null

        return MatchCandidate(
            rect = Rect(bestX, bestY, bestX + w, bestY + h),
            score = bestScore
        )
    }

    private fun rankCandidates(
        candidates: List<MatchCandidate>,
        modes: SearchModes
    ): List<MatchCandidate> {

        val sorted = candidates.sortedByDescending { it.score }

        return if (modes.exactMatchOnly) {
            sorted.filter { it.score > 0.92f }
        } else {
            sorted
        }
    }

    private fun fastCompare(
        frame: Bitmap,
        mask: Bitmap,
        x: Int,
        y: Int
    ): Float {
        var score = 0f
        val w = mask.width
        val h = mask.height

        for (dy in 0 until h step 3) {
            for (dx in 0 until w step 3) {
                if (x + dx < frame.width && y + dy < frame.height) {
                    if (frame.getPixel(x + dx, y + dy) == mask.getPixel(dx, dy)) {
                        score += 0.01f
                    }
                }
            }
        }

        return score.coerceIn(0f, 1f)
    }

    private fun preciseCompare(
        frame: Bitmap,
        mask: Bitmap,
        x: Int,
        y: Int
    ): Float {
        var score = 0f
        val w = mask.width
        val h = mask.height

        for (dy in 0 until h step 2) {
            for (dx in 0 until w step 2) {
                if (x + dx < frame.width && y + dy < frame.height) {
                    if (frame.getPixel(x + dx, y + dy) == mask.getPixel(dx, dy)) {
                        score += 0.005f
                    }
                }
            }
        }

        return score.coerceIn(0f, 1f)
    }
}
