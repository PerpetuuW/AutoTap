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

        val scales = if (modes.multiScaleSearch) {
            floatArrayOf(1.0f, 0.85f, 1.15f)
        } else {
            floatArrayOf(1.0f)
        }

        for (scale in scales) {
            val scaledMask = if (scale != 1.0f) {
                val targetW = (mask.width * scale).toInt().coerceAtLeast(4)
                val targetH = (mask.height * scale).toInt().coerceAtLeast(4)
                if (targetW < frame.width && targetH < frame.height) {
                    Bitmap.createScaledBitmap(mask, targetW, targetH, true)
                } else null
            } else mask

            if (scaledMask == null || scaledMask.isRecycled) continue

            val matchResults = matchInternal(frame, scaledMask, searchArea, modes, threshold, scale)
            candidates.addAll(matchResults)

            if (scaledMask != mask) {
                scaledMask.recycle()
            }
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun matchInternal(
        frame: Bitmap,
        mask: Bitmap,
        searchArea: Rect,
        modes: SearchModes,
        threshold: Float,
        scale: Float
    ): List<MatchCandidate> {
        val candidates = mutableListOf<MatchCandidate>()

        val safeSearchArea = Rect(
            searchArea.left.coerceIn(0, frame.width),
            searchArea.top.coerceIn(0, frame.height),
            searchArea.right.coerceIn(0, frame.width),
            searchArea.bottom.coerceIn(0, frame.height)
        )

        // 💥 ОПТИМИЗИРОВАННЫЙ ШАГ СКАНИРОВАНИЯ ПОД FULL HD (1080x2400) -> 80-120мс!
        val coarseStep = if (modes.hybridCascadeMode) {
            (maxOf(mask.width, mask.height) / 10).coerceIn(4, 12)
        } else 2

        val startX = safeSearchArea.left
        val startY = safeSearchArea.top
        val endX = (safeSearchArea.right - mask.width).coerceAtLeast(startX)
        val endY = (safeSearchArea.bottom - mask.height).coerceAtLeast(startY)

        if (endX <= startX || endY <= startY) return candidates

        val coarseThreshold = (threshold - 0.35f).coerceAtLeast(0.40f)
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
                        candidates.add(MatchCandidate(pt, exactScore, bbox, scale, 0))
                    }
                }
            }
        }

        return candidates
    }

    private fun comparePixelsWithTolerance(frame: Bitmap, mask: Bitmap, x: Int, y: Int): Float {
        if (frame.isRecycled || mask.isRecycled) return 0f
        var totalDiff = 0L
        var pixelCount = 0

        val stepX = (mask.width / 14).coerceAtLeast(1)
        val stepY = (mask.height / 14).coerceAtLeast(1)

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

                val diffR = abs(fr - mr).let { if (it <= 16) 0 else it - 16 }
                val diffG = abs(fg - mg).let { if (it <= 16) 0 else it - 16 }
                val diffB = abs(fb - mb).let { if (it <= 16) 0 else it - 16 }

                totalDiff += diffR + diffG + diffB
                pixelCount++

                my += stepY
            }
            mx += stepX
        }

        if (pixelCount == 0) return 1.0f
        val maxDiff = pixelCount * 230f * 3f
        val similarity = 1.0f - (totalDiff.toFloat() / maxDiff)
        return similarity.coerceIn(0f, 1f)
    }

    private fun compareEdges(frame: Bitmap, mask: Bitmap, x: Int, y: Int): Float {
        if (frame.isRecycled || mask.isRecycled) return 0f
        var edgeDiff = 0L
        var count = 0
        val stepX = (mask.width / 10).coerceAtLeast(1)
        val stepY = (mask.height / 10).coerceAtLeast(1)

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
        val p1 = getLuminance(bmp.getPixel(x - 1, y))
        val p2 = getLuminance(bmp.getPixel(x + 1, y))
        val p3 = getLuminance(bmp.getPixel(x, y - 1))
        val p4 = getLuminance(bmp.getPixel(x, y + 1))
        return abs(p2 - p1) + abs(p4 - p3)
    }

    private fun getLuminance(pixel: Int): Int {
        val r = (pixel shr 16) and 0xFF
        val g = (pixel shr 8) and 0xFF
        val b = pixel and 0xFF
        return (r * 77 + g * 150 + b * 29) shr 8
    }
}
