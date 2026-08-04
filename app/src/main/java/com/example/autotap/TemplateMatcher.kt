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
)

object TemplateMatcher {

    // ---------------------------------------------------------
    // Основной поиск: Coarse → Fine
    // ---------------------------------------------------------
    fun findTemplateCandidatesCoarseFine(
        screen: Bitmap,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): List<MatchCandidate> {

        val similarityThreshold = (config.similarityPercent / 100f).coerceIn(0.1f, 0.99f)
        val shapeOnly = config.shapeOnlyMode
        val hybridCascade = config.hybridCascadeMode
        val multiScale = config.multiScaleSearch

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

        val coarseStep = 6
        val fineStep = 2

        val scales = if (multiScale) {
            floatArrayOf(1.0f, 0.95f, 0.9f, 1.05f)
        } else {
            floatArrayOf(1.0f)
        }

        for (scale in scales) {
            val scaledTemplate = if (scale != 1.0f) {
                Bitmap.createScaledBitmap(
                    template,
                    (template.width * scale).toInt(),
                    (template.height * scale).toInt(),
                    true
                )
            } else template

            val tw = scaledTemplate.width
            val th = scaledTemplate.height

            // -----------------------------
            // COARSE PASS
            // -----------------------------
            for (y in searchArea.top until searchArea.bottom - th step coarseStep) {
                for (x in searchArea.left until searchArea.right - tw step coarseStep) {

                    val score = if (shapeOnly) {
                        shapeMatch(screen, scaledTemplate, x, y)
                    } else {
                        pixelMatch(screen, scaledTemplate, x, y)
                    }

                    if (score >= similarityThreshold) {
                        candidates.add(MatchCandidate(Rect(x, y, x + tw, y + th), score))
                    }
                }
            }

            // -----------------------------
            // FINE PASS
            // -----------------------------
            val refined = ArrayList<MatchCandidate>()
            for (c in candidates) {
                val cx0 = max(searchArea.left, c.rect.left - coarseStep)
                val cy0 = max(searchArea.top, c.rect.top - coarseStep)
                val cx1 = min(searchArea.right - tw, c.rect.left + coarseStep)
                val cy1 = min(searchArea.bottom - th, c.rect.top + coarseStep)

                var bestScore = c.score
                var bestRect = c.rect

                for (y in cy0..cy1 step fineStep) {
                    for (x in cx0..cx1 step fineStep) {
                        val score = if (shapeOnly) {
                            shapeMatch(screen, scaledTemplate, x, y)
                        } else {
                            pixelMatch(screen, scaledTemplate, x, y)
                        }
                        if (score > bestScore) {
                            bestScore = score
                            bestRect = Rect(x, y, x + tw, y + th)
                        }
                    }
                }

                refined.add(MatchCandidate(bestRect, bestScore))
            }

            candidates.clear()
            candidates.addAll(refined)
        }

        if (hybridCascade) {
            return candidates.sortedByDescending { it.score }.take(3)
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun pixelMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th) {
            for (x in 0 until tw) {
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val dr = abs(Color.red(sc) - Color.red(tc))
                val dg = abs(Color.green(sc) - Color.green(tc))
                val db = abs(Color.blue(sc) - Color.blue(tc))

                val diff = (dr + dg + db) / 765f
                val sim = 1f - diff

                score += sim
                total += 1f
            }
        }

        return score / total
    }

    private fun shapeMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th step 2) {
            for (x in 0 until tw step 2) {
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val scA = Color.alpha(sc)
                val tcA = Color.alpha(tc)

                val sim = if (tcA < 128) {
                    if (scA < 128) 1f else 0f
                } else {
                    if (scA >= 128) 1f else 0f
                }

                score += sim
                total += 1f
            }
        }

        return score / total
    }

    fun aggregateMultiFrameMask(frames: List<Bitmap>, circleShape: Boolean): Bitmap {
        if (frames.isEmpty()) return Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)

        val w = frames[0].width
        val h = frames[0].height

        val out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)

        for (y in 0 until h) {
            for (x in 0 until w) {

                var sumR = 0
                var sumG = 0
                var sumB = 0
                var sumA = 0

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

                val finalColor = Color.argb(avgA, avgR, avgG, avgB)
                out.setPixel(x, y, finalColor)
            }
        }

        if (circleShape) {
            applyCircularMask(out)
        }

        return out
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
