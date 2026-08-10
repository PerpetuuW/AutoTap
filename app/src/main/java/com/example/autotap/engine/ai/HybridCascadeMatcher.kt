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

        if (frame.isRecycled || mask.isRecycled) return candidates
        if (mask.width < 2 || mask.height < 2 || frame.width < 2 || frame.height < 2) return candidates

        val safeSearchArea = Rect(
            searchArea.left.coerceIn(0, frame.width),
            searchArea.top.coerceIn(0, frame.height),
            searchArea.right.coerceIn(0, frame.width),
            searchArea.bottom.coerceIn(0, frame.height)
        )

        val coarseStep = if (modes.hybridCascadeMode) {
            when (modes.profile) {
                TemplateProfile.SMALL -> 2
                TemplateProfile.LARGE -> 6
                TemplateProfile.THIN_LINE -> 1
                else -> 4
            }
        } else 1

        val startX = safeSearchArea.left
        val startY = safeSearchArea.top
        val endX = (safeSearchArea.right - mask.width).coerceAtLeast(startX)
        val endY = (safeSearchArea.bottom - mask.height).coerceAtLeast(startY)

        if (endX <= startX || endY <= startY) return candidates

        // ФАЗА 1: Грубое быстрое сканирование (Порог 50%)
        val coarseThreshold = (threshold - 0.30f).coerceAtLeast(0.50f)
        val potentialHits = mutableListOf<PointF>()

        var x = startX
        while (x <= endX) {
            var y = startY
            while (y <= endY) {
                if (frame.isRecycled || mask.isRecycled) break

                val pixelScore = comparePixelsWithTolerance(frame, mask, x, y)
                val contourScore = compareEdges(frame, mask, x, y)
                val coarseScore = (contourScore * 0.4f) + (pixelScore * 0.6f)

                if (coarseScore >= coarseThreshold) {
                    potentialHits.add(PointF(x.toFloat(), y.toFloat()))
                }
                y += coarseStep
            }
            x += coarseStep
        }

        // ФАЗА 2: Точнейшая доводка с шагом 1 пиксель (1px Fine Refinement)
        val fineWindow = coarseStep + 2
        val visitedPoints = HashSet<Long>()

        for (hit in potentialHits) {
            val fxStart = (hit.x.toInt() - fineWindow).coerceIn(startX, endX)
            val fxEnd = (hit.x.toInt() + fineWindow).coerceIn(startX, endX)
            val fyStart = (hit.y.toInt() - fineWindow).coerceIn(startY, endY)
            val fyEnd = (hit.y.toInt() + fineWindow).coerceIn(startY, endY)

            for (fx in fxStart..fxEnd) {
                for (fy in fyStart..fyEnd) {
                    val pointKey = (fx.toLong() shl 32) or (fy.toLong() and 0xFFFFFFFFL)
                    if (visitedPoints.contains(pointKey)) continue
                    visitedPoints.add(pointKey)

                    val pixelScore = comparePixelsWithTolerance(frame, mask, fx, fy)
                    val contourScore = compareEdges(frame, mask, fx, fy)
                    val exactScore = (contourScore * 0.4f) + (pixelScore * 0.6f)

                    if (exactScore >= threshold) {
                        val pt = PointF(fx + mask.width / 2f, fy + mask.height / 2f)
                        val bbox = Rect(fx, fy, fx + mask.width, fy + mask.height)
                        candidates.add(MatchCandidate(pt, exactScore, bbox, 1.0f, 0))
                    }
                }
            }
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun comparePixelsWithTolerance(frame: Bitmap, mask: Bitmap, x: Int, y: Int): Float {
        if (frame.isRecycled || mask.isRecycled) return 0f
        var totalDiff = 0L
        var pixelCount = 0

        val stepX = (mask.width / 16).coerceAtLeast(1)
        val stepY = (mask.height / 16).coerceAtLeast(1)

        var mx = 0
        while (mx < mask.width) {
            var my = 0
            while (my < mask.height) {
                val fx = x + mx
                val fy = y + my
                if (fx >= frame.width || fy >= frame.height) {
                    my += stepY
                    continue
                }

                val framePixel = frame.getPixel(fx, fy)
                val maskPixel = mask.getPixel(mx, my)

                val ma = (maskPixel shr 24) and 0xFF
                if (ma < 30) {
                    my += stepY
                    continue
                }

                val fr = (framePixel shr 16) and 0xFF
                val fg = (framePixel shr 8) and 0xFF
                val fb = framePixel and 0xFF

                val mr = (maskPixel shr 16) and 0xFF
                val mg = (maskPixel shr 8) and 0xFF
                val mb = maskPixel and 0xFF

                val diffR = abs(fr - mr).let { if (it <= 12) 0 else it - 12 }
                val diffG = abs(fg - mg).let { if (it <= 12) 0 else it - 12 }
                val diffB = abs(fb - mb).let { if (it <= 12) 0 else it - 12 }

                totalDiff += diffR + diffG + diffB
                pixelCount++

                my += stepY
            }
            mx += stepX
        }

        if (pixelCount == 0) return 1.0f
        val maxDiff = pixelCount * 240f * 3f
        val similarity = 1.0f - (totalDiff.toFloat() / maxDiff)
        return similarity.coerceIn(0f, 1f)
    }

    private fun compareEdges(frame: Bitmap, mask: Bitmap, x: Int, y: Int): Float {
        if (frame.isRecycled || mask.isRecycled) return 0f
        var edgeDiff = 0L
        var count = 0
        val stepX = (mask.width / 12).coerceAtLeast(1)
        val stepY = (mask.height / 12).coerceAtLeast(1)

        var mx = 1
        while (mx < mask.width - 1) {
            var my = 1
            while (my < mask.height - 1) {
                val fx = x + mx
                val fy = y + my
                if (fx <= 0 || fx >= frame.width - 1 || fy <= 0 || fy >= frame.height - 1) {
                    my += stepY
                    continue
                }

                val maskGrad = getGradient(mask, mx, my)
                val frameGrad = getGradient(frame, fx, fy)

                edgeDiff += abs(maskGrad - frameGrad)
                count++
                my += stepY
            }
            mx += stepX
        }

        if (count == 0) return 1.0f
        val maxGradDiff = count * 255f
        return (1.0f - (edgeDiff.toFloat() / maxGradDiff)).coerceIn(0f, 1f)
    }

    private fun getGradient(bmp: Bitmap, x: Int, y: Int): Int {
        if (bmp.isRecycled || x <= 0 || x >= bmp.width - 1 || y <= 0 || y >= bmp.height - 1) return 0
        val p1 = bmp.getPixel(x - 1, y) and 0xFF
        val p2 = bmp.getPixel(x + 1, y) and 0xFF
        val p3 = bmp.getPixel(x, y - 1) and 0xFF
        val p4 = bmp.getPixel(x, y + 1) and 0xFF
        return abs(p2 - p1) + abs(p4 - p3)
    }
}
