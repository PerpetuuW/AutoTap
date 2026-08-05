package com.example.autotap

import android.graphics.*
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

data class MatchCandidate(
    val rect: Rect,
    val score: Float,
    val templateIndex: Int = -1
) {
    val point: PointF
        get() = PointF(rect.centerX().toFloat(), rect.centerY().toFloat())
}

object TemplateMatcher {

    fun analyzeTemplate(template: Bitmap): JSONObject {
        return JSONObject().apply {
            put("width", template.width)
            put("height", template.height)
        }
    }

    fun generateSmartMask(src: Bitmap, isCircle: Boolean): Bitmap {
        val out = src.copy(Bitmap.Config.ARGB_8888, true)
        if (isCircle) {
            applyCircularMask(out)
        }
        return out
    }

    fun aggregateMultiFrameMask(frames: List<Bitmap>, circleShape: Boolean): Bitmap {
        if (frames.isEmpty()) return Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)

        val w = frames[0].width
        val h = frames[0].height

        val out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)

        for (y in 0 until h) {
            for (x in 0 until w) {
                var sumR = 0; var sumG = 0; var sumB = 0; var sumA = 0
                for (bmp in frames) {
                    val c = bmp.getPixel(x, y)
                    sumR += Color.red(c)
                    sumG += Color.green(c)
                    sumB += Color.blue(c)
                    sumA += Color.alpha(c)
                }
                val avgR = sumR / frames.size
                val avgG = sumG / frames.size
                val avgB = sumB / frames.size
                val avgA = sumA / frames.size

                out.setPixel(x, y, Color.argb(avgA, avgR, avgG, avgB))
            }
        }

        if (circleShape) applyCircularMask(out)
        return out
    }

    fun findCandidatesForCreation(screenBitmap: Bitmap, template: Bitmap): MutableList<MatchCandidate> {
        val list = ArrayList<MatchCandidate>()
        list.add(MatchCandidate(Rect(0, 0, template.width, template.height), 1.0f))
        return list
    }

    fun findTemplateCandidatesCoarseFine(
        screen: Bitmap,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): List<MatchCandidate> {

        val similarityThreshold = (config.similarityPercent / 100f).coerceIn(0.1f, 0.99f)
        val candidates = ArrayList<MatchCandidate>()

        val searchArea = if (config.customSearchArea) {
            Rect(
                (config.searchAreaXNorm * screen.width).toInt().coerceIn(0, screen.width - 1),
                (config.searchAreaYNorm * screen.height).toInt().coerceIn(0, screen.height - 1),
                ((config.searchAreaXNorm + config.searchAreaWNorm) * screen.width).toInt().coerceIn(1, screen.width),
                ((config.searchAreaYNorm + config.searchAreaHNorm) * screen.height).toInt().coerceIn(1, screen.height)
            )
        } else {
            Rect(0, 0, screen.width, screen.height)
        }

        val tw = template.width
        val th = template.height

        for (y in searchArea.top until (searchArea.bottom - th).coerceAtLeast(searchArea.top + 1) step 6) {
            for (x in searchArea.left until (searchArea.right - tw).coerceAtLeast(searchArea.left + 1) step 6) {
                val score = pixelMatch(screen, template, x, y)
                if (score >= similarityThreshold) {
                    candidates.add(MatchCandidate(Rect(x, y, x + tw, y + th), score))
                }
            }
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun pixelMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th step 2) {
            for (x in 0 until tw step 2) {
                if (sx + x >= screen.width || sy + y >= screen.height) continue
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val dr = abs(Color.red(sc) - Color.red(tc))
                val dg = abs(Color.green(sc) - Color.green(tc))
                val db = abs(Color.blue(sc) - Color.blue(tc))

                val diff = (dr + dg + db) / 765f
                score += (1f - diff)
                total += 1f
            }
        }

        return if (total > 0f) score / total else 0f
    }

    private fun applyCircularMask(bmp: Bitmap) {
        val w = bmp.width
        val h = bmp.height
        val cx = w / 2f
        val cy = h / 2f
        val r = min(w, h) / 2f

        for (y in 0 until h) {
            for (x in 0 until w) {
                val dx = x - cx
                val dy = y - cy
                if (dx * dx + dy * dy > r * r) {
                    bmp.setPixel(x, y, Color.TRANSPARENT)
                }
            }
        }
    }
}
