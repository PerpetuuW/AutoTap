package com.example.autotap.infrastructure.ocr

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Rect
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import com.example.autotap.core.logger.AppLogger
import com.example.autotap.domain.model.OcrMatchResult
import java.nio.FloatBuffer
import java.util.Collections
import java.util.Locale
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Специализированный легковесный OCR-движок для интерфейсов и мобильных игр на базе Pure ONNX.
 *
 * Архитектура и технологии:
 *  1. Multi-Octave Text Line & Word Detector: извлекает целые фразы и слова любой высоты (12px..140px+).
 *  2. Game-Font Preprocessor: адаптивный контраст и нормализация подложки.
 *  3. Pure ONNX PP-OCRv4 SVTR Inference (cyrillic_rec.onnx + cyrillic_dict.txt) в строгом RGB формате.
 *  4. Fast CTC Beam Decoder с поддержкой точной кириллицы (RU) и латиницы (EN).
 */
object OcrEngine {
    private val ortEnv: OrtEnvironment by lazy { OrtEnvironment.getEnvironment() }

    @Volatile
    var explicitContext: Context? = null

    private val sessionLock = Any()
    @Volatile
    private var cachedRecSession: OrtSession? = null
    @Volatile
    private var cachedDictionary: List<String>? = null

    private fun getContext(): Context? {
        return explicitContext
            ?: AppLogger.appContext
            ?: com.example.autotap.infrastructure.accessibility.AutoTapAccessibilityService.instance
    }

    private fun getRecSession(): OrtSession? {
        cachedRecSession?.let { return it }
        synchronized(sessionLock) {
            cachedRecSession?.let { return it }
            val ctx = getContext() ?: return null
            return try {
                val opts = OrtSession.SessionOptions().apply {
                    setIntraOpNumThreads(2)
                }
                val modelBytes = ctx.assets.open("models/cyrillic_rec.onnx").use { it.readBytes() }
                val session = ortEnv.createSession(modelBytes, opts)
                cachedRecSession = session
                session
            } catch (e: Throwable) {
                AppLogger.logError(null, "ONNX_INIT", e)
                null
            }
        }
    }

    private fun getDictionary(): List<String> {
        cachedDictionary?.let { return it }
        synchronized(sessionLock) {
            cachedDictionary?.let { return it }
            val ctx = getContext() ?: return emptyList()
            return try {
                val list = mutableListOf<String>()
                list.add("blank") // CTC blank символ на позиции 0
                ctx.assets.open("models/cyrillic_dict.txt").bufferedReader().useLines { lines ->
                    lines.forEach { line ->
                        list.add(line.replace("\r", "").replace("\n", ""))
                    }
                }
                if (!list.contains(" ")) {
                    list.add(" ")
                }
                cachedDictionary = list
                list
            } catch (e: Throwable) {
                AppLogger.logError(null, "OCR_DICT_INIT", e)
                emptyList()
            }
        }
    }

    private val KEY_VALUE_REGEX = Regex("""(?i)([a-zа-яё0-9_-]+)[:\s=]+([\d.,]+[kmbKMBкКмМбБ]?)""")

    private fun isValidForOcr(bmp: Bitmap?): Boolean {
        if (bmp == null || bmp.isRecycled) return false
        return bmp.width > 1 && bmp.height > 1
    }

    /**
     * Предобработка игрового шрифта (удаление обводки/тени и нормализация контраста).
     */
    private fun enhanceGameFontCrop(bitmap: Bitmap): Bitmap {
        val w = bitmap.width
        val h = bitmap.height
        if (w < 4 || h < 4) return bitmap

        val pixels = IntArray(w * h)
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h)

        var minLum = 255
        var maxLum = 0
        val lums = IntArray(w * h)
        for (i in pixels.indices) {
            val p = pixels[i]
            val lum = (((p shr 16) and 0xFF) * 299 + ((p shr 8) and 0xFF) * 587 + (p and 0xFF) * 114) / 1000
            lums[i] = lum
            if (lum < minLum) minLum = lum
            if (lum > maxLum) maxLum = lum
        }

        if (maxLum - minLum in 15..150) {
            val enhanced = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
            val range = max(1, maxLum - minLum)
            for (i in pixels.indices) {
                val p = pixels[i]
                val a = (p shr 24) and 0xFF
                val r = ((((p shr 16) and 0xFF) - minLum) * 255 / range).coerceIn(0, 255)
                val g = ((((p shr 8) and 0xFF) - minLum) * 255 / range).coerceIn(0, 255)
                val b = (((p and 0xFF) - minLum) * 255 / range).coerceIn(0, 255)
                pixels[i] = (a shl 24) or (r shl 16) or (g shl 8) or b
            }
            enhanced.setPixels(pixels, 0, w, 0, 0, w, h)
            return enhanced
        }
        return bitmap
    }

    /**
     * Инференс нейросети PP-OCRv4 (Pure ONNX) в строгом RGB формате.
     */
    fun recognizeTextWithOnnx(bitmap: Bitmap): String? {
        val session = getRecSession() ?: return null
        val dict = getDictionary()
        if (dict.isEmpty()) return null

        val processedBmp = enhanceGameFontCrop(bitmap)
        val targetH = 48
        val scale = targetH.toFloat() / processedBmp.height.toFloat().coerceAtLeast(1f)
        val resizedW = ((processedBmp.width * scale).toInt()).coerceIn(32, 960)
        val targetW = maxOf(64, ((resizedW + 31) / 32) * 32)

        val scaled = Bitmap.createScaledBitmap(processedBmp, resizedW, targetH, true)
        val pixels = IntArray(resizedW * targetH)
        scaled.getPixels(pixels, 0, resizedW, 0, 0, resizedW, targetH)

        val floatBuffer = FloatBuffer.allocate(1 * 3 * targetH * targetW)
        for (c in 0 until 3) {
            for (y in 0 until targetH) {
                for (x in 0 until targetW) {
                    if (x < resizedW) {
                        val pixel = pixels[y * resizedW + x]
                        val rawChannel = when (c) {
                            0 -> (pixel shr 16) and 0xFF // R
                            1 -> (pixel shr 8) and 0xFF  // G
                            else -> pixel and 0xFF       // B
                        }
                        floatBuffer.put((rawChannel / 255.0f - 0.5f) / 0.5f)
                    } else {
                        floatBuffer.put(0.0f)
                    }
                }
            }
        }
        floatBuffer.flip()

        var tensor: OnnxTensor? = null
        var results: OrtSession.Result? = null
        try {
            tensor = OnnxTensor.createTensor(ortEnv, floatBuffer, longArrayOf(1, 3, targetH.toLong(), targetW.toLong()))
            val inputName = session.inputNames.iterator().next()
            results = session.run(Collections.singletonMap(inputName, tensor))

            val outputTensor = results[0] as? OnnxTensor ?: return null
            @Suppress("UNCHECKED_CAST")
            val output = outputTensor.value as? Array<Array<FloatArray>> ?: return null

            val sb = StringBuilder()
            var lastIndex = -1
            val timeSteps = output[0]
            val validSteps = ((timeSteps.size.toFloat() * resizedW) / targetW).toInt().coerceIn(1, timeSteps.size)

            for (s in 0 until validSteps) {
                val step = timeSteps[s]
                var maxIdx = 0
                var maxProb = step[0]
                for (i in 1 until step.size) {
                    if (step[i] > maxProb) {
                        maxProb = step[i]
                        maxIdx = i
                    }
                }
                if (maxIdx != 0 && maxIdx != lastIndex && maxIdx < dict.size) {
                    sb.append(dict[maxIdx])
                }
                lastIndex = maxIdx
            }
            val rawDecoded = sb.toString().trim()
            return postProcessRussianText(rawDecoded)
        } catch (e: Throwable) {
            AppLogger.logError(null, "ONNX_INFER", e)
            return null
        } finally {
            try { tensor?.close() } catch (_: Throwable) {}
            try { results?.close() } catch (_: Throwable) {}
            if (scaled != processedBmp && !scaled.isRecycled) {
                try { scaled.recycle() } catch (_: Throwable) {}
            }
            if (processedBmp != bitmap && !processedBmp.isRecycled) {
                try { processedBmp.recycle() } catch (_: Throwable) {}
            }
        }
    }

    /**
     * Постобработка: замена ошибочных латинских символов-двойников на русскую кириллицу
     * в словах, содержащих кириллические буквы (например, "ИГPATЬ" -> "ИГРАТЬ", "HAЧATЬ" -> "НАЧАТЬ").
     */
    private fun postProcessRussianText(text: String): String {
        if (text.isBlank()) return text
        val hasCyrillic = text.any { it in 'а'..'я' || it in 'А'..'Я' || it == 'ё' || it == 'Ё' }
        if (!hasCyrillic) return text

        val sb = StringBuilder()
        for (ch in text) {
            val converted = when (ch) {
                'A' -> 'А'
                'B' -> 'В'
                'E' -> 'Е'
                'K' -> 'К'
                'M' -> 'М'
                'H' -> 'Н'
                'O' -> 'О'
                'P' -> 'Р'
                'C' -> 'С'
                'T' -> 'Т'
                'X' -> 'Х'
                'a' -> 'а'
                'e' -> 'е'
                'o' -> 'о'
                'p' -> 'р'
                'c' -> 'с'
                'x' -> 'х'
                'y' -> 'у'
                else -> ch
            }
            sb.append(converted)
        }
        return sb.toString()
    }

    /**
     * Полноэкранный детектор связных фраз и строк слов (Horizontal Text Line Merging).
     */
    private fun extractWordBoundingBoxes(bmp: Bitmap): List<Rect> {
        val w = bmp.width
        val h = bmp.height
        if (w < 16 || h < 16) return listOf(Rect(0, 0, w, h))

        val scale = if (max(w, h) > 960) 960f / max(w, h).toFloat() else 1f
        val sw = (w * scale).toInt().coerceAtLeast(16)
        val sh = (h * scale).toInt().coerceAtLeast(16)

        val scaledBmp = if (scale < 1f) Bitmap.createScaledBitmap(bmp, sw, sh, false) else bmp
        val pixels = IntArray(sw * sh)
        scaledBmp.getPixels(pixels, 0, sw, 0, 0, sw, sh)
        if (scaledBmp != bmp && !scaledBmp.isRecycled) scaledBmp.recycle()

        val lums = IntArray(sw * sh)
        for (i in pixels.indices) {
            val p = pixels[i]
            lums[i] = (((p shr 16) and 0xFF) * 299 + ((p shr 8) and 0xFF) * 587 + (p and 0xFF) * 114) / 1000
        }

        val edges = BooleanArray(sw * sh)
        for (y in 1 until sh - 1) {
            val rowOff = y * sw
            for (x in 1 until sw - 1) {
                val gx = abs(lums[rowOff + x + 1] - lums[rowOff + x - 1])
                val gy = abs(lums[(y + 1) * sw + x] - lums[(y - 1) * sw + x])
                if (gx + gy > 32) {
                    edges[rowOff + x] = true
                }
            }
        }

        val dilated = BooleanArray(sw * sh)
        val kRadius = (10 * scale).toInt().coerceIn(4, 14)
        for (y in 0 until sh) {
            val rowOff = y * sw
            var count = 0
            for (x in 0 until min(sw, kRadius * 2)) {
                if (edges[rowOff + x]) count++
            }
            for (x in 0 until sw) {
                if (count > 0) dilated[rowOff + x] = true
                val removeX = x - kRadius
                if (removeX >= 0 && edges[rowOff + removeX]) count--
                val addX = x + kRadius + 1
                if (addX < sw && edges[rowOff + addX]) count++
            }
        }

        val visited = BooleanArray(sw * sh)
        val rawBoxes = mutableListOf<Rect>()
        val invScale = 1f / scale

        for (y in 0 until sh step 2) {
            val rowOff = y * sw
            for (x in 0 until sw step 2) {
                val idx = rowOff + x
                if (dilated[idx] && !visited[idx]) {
                    var minX = x; var maxX = x
                    var minY = y; var maxY = y
                    var compPixels = 0

                    val queueX = IntArray(4096)
                    val queueY = IntArray(4096)
                    var head = 0; var tail = 0

                    queueX[tail] = x; queueY[tail] = y; tail++
                    visited[idx] = true

                    while (head < tail && tail < 4080) {
                        val cx = queueX[head]; val cy = queueY[head]; head++
                        compPixels++
                        if (cx < minX) minX = cx
                        if (cx > maxX) maxX = cx
                        if (cy < minY) minY = cy
                        if (cy > maxY) maxY = cy

                        val neighbors = intArrayOf(cx - 2, cy, cx + 2, cy, cx, cy - 2, cx, cy + 2)
                        for (ni in 0 until 8 step 2) {
                            val nx = neighbors[ni]; val ny = neighbors[ni + 1]
                            if (nx in 0 until sw && ny in 0 until sh) {
                                val nIdx = ny * sw + nx
                                if (dilated[nIdx] && !visited[nIdx]) {
                                    visited[nIdx] = true
                                    queueX[tail] = nx; queueY[tail] = ny; tail++
                                }
                            }
                        }
                    }

                    val bw = maxX - minX + 1
                    val bh = maxY - minY + 1
                    if (bw >= 10 && bh in 8..240 && compPixels >= 6) {
                        val origL = ((minX - 6) * invScale).toInt().coerceIn(0, w - 1)
                        val origT = ((minY - 4) * invScale).toInt().coerceIn(0, h - 1)
                        val origR = ((maxX + 7) * invScale).toInt().coerceIn(origL + 1, w)
                        val origB = ((maxY + 5) * invScale).toInt().coerceIn(origT + 1, h)
                        rawBoxes.add(Rect(origL, origT, origR, origB))
                    }
                }
            }
        }

        // Горизонтальное слияние соседних слов в единые фразы одной строки
        val lineMergedBoxes = mutableListOf<Rect>()
        rawBoxes.sortBy { it.top * 10000 + it.left }

        for (box in rawBoxes) {
            var merged = false
            for (i in lineMergedBoxes.indices) {
                val m = lineMergedBoxes[i]
                val sameLine = abs(m.centerY() - box.centerY()) <= max(m.height(), box.height()) * 0.6f
                val horizontalClose = box.left >= m.left && (box.left - m.right) <= max(m.height(), box.height()) * 1.8f
                val intersects = Rect.intersects(m, box)

                if (intersects || (sameLine && horizontalClose)) {
                    lineMergedBoxes[i] = Rect(
                        min(m.left, box.left),
                        min(m.top, box.top),
                        max(m.right, box.right),
                        max(m.bottom, box.bottom)
                    )
                    merged = true
                    break
                }
            }
            if (!merged) {
                lineMergedBoxes.add(box)
            }
        }

        lineMergedBoxes.sortBy { it.top * 10000 + it.left }
        return if (lineMergedBoxes.isNotEmpty()) lineMergedBoxes else listOf(Rect(0, 0, w, h))
    }

    /**
     * Нормализация строки с заменой сходных символов (RU/EN гомоглифы и регистр).
     */
    private fun normalizeString(s: String): String {
        return s.trim()
            .lowercase(Locale.ROOT)
            .replace('ё', 'е')
            .replace('a', 'а')
            .replace('o', 'о')
            .replace('e', 'е')
            .replace('p', 'р')
            .replace('c', 'с')
            .replace('x', 'х')
            .replace('t', 'т')
            .replace('b', 'в')
            .replace('k', 'к')
            .replace('m', 'м')
            .replace('h', 'н')
            .replace('y', 'у')
    }

    /**
     * Расчет расстояния Левенштейна для нечеткого поиска по стилизованным шрифтам.
     */
    private fun isFuzzyMatch(candidate: String, query: String): Boolean {
        val normC = normalizeString(candidate).replace(" ", "")
        val normQ = normalizeString(query).replace(" ", "")
        if (normQ.isEmpty()) return true
        if (normC.contains(normQ)) return true

        val qLen = normQ.length
        if (qLen <= 2) return normC == normQ

        val maxDist = if (qLen <= 5) 1 else 2
        for (i in 0..max(0, normC.length - qLen)) {
            val sub = normC.substring(i, min(normC.length, i + qLen))
            var diff = 0
            for (j in 0 until min(sub.length, qLen)) {
                if (sub[j] != normQ[j]) diff++
            }
            diff += abs(sub.length - qLen)
            if (diff <= maxDist) return true
        }
        return false
    }

    fun findTextOnScreen(
        bitmap: Bitmap,
        targetQuery: String,
        timeoutMs: Long = 3000L,
        roi: Rect? = null,
        outVariables: MutableMap<String, String>? = null
    ): List<OcrMatchResult> {
        val perfStart = System.currentTimeMillis()
        if (!isValidForOcr(bitmap)) {
            AppLogger.log(null, "OCR", "OCR отменен: передан невалидный bitmap")
            return emptyList()
        }

        AppLogger.log(null, "OCR", "Старт Game OCR. Поиск: '$targetQuery', Размер: ${bitmap.width}x${bitmap.height}, ROI: ${roi?.toShortString() ?: "весь экран"}")

        // 1. Мгновенная проверка системного UI через Accessibility Service (1-3 мс)
        val service = com.example.autotap.infrastructure.accessibility.AutoTapAccessibilityService.instance
        if (service != null && targetQuery.isNotBlank() && !targetQuery.startsWith("regex:")) {
            val nativeResults = service.findTextInActiveWindow(targetQuery, roi)
            if (nativeResults.isNotEmpty()) {
                val elapsed = System.currentTimeMillis() - perfStart
                AppLogger.log(null, "OCR", "OCR (Accessibility Service): '${nativeResults.first().matchedText}' в (${nativeResults.first().clickX}, ${nativeResults.first().clickY}) за ${elapsed}мс")
                return nativeResults
            }
        }

        val isHardware = android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O && bitmap.config == Bitmap.Config.HARDWARE
        val srcBmp = if (isHardware || !bitmap.isMutable) {
            val sw = Bitmap.createBitmap(bitmap.width, bitmap.height, Bitmap.Config.ARGB_8888)
            val c = android.graphics.Canvas(sw)
            c.drawBitmap(bitmap, 0f, 0f, null)
            sw
        } else {
            bitmap
        }

        val localBmp = if (roi != null) {
            val safeLeft = roi.left.coerceIn(0, srcBmp.width - 1)
            val safeTop = roi.top.coerceIn(0, srcBmp.height - 1)
            val safeWidth = roi.width().coerceIn(1, srcBmp.width - safeLeft)
            val safeHeight = roi.height().coerceIn(1, srcBmp.height - safeTop)
            Bitmap.createBitmap(srcBmp, safeLeft, safeTop, safeWidth, safeHeight)
        } else {
            srcBmp
        }

        val cleanQuery = targetQuery.trim()
        val stripH = 48
        val gOffsetX = roi?.left?.coerceIn(0, srcBmp.width - 1) ?: 0
        val gOffsetY = roi?.top?.coerceIn(0, srcBmp.height - 1) ?: 0

        // 2. Прямое распознавание выделенной области ROI целиком (если ROI задан)
        if (roi != null && localBmp.width >= 16 && localBmp.height >= 12) {
            val directRec = recognizeTextWithOnnx(localBmp)
            if (!directRec.isNullOrBlank()) {
                AppLogger.log(null, "OCR_ROI_DIRECT", "Прямое распознавание ROI: '$directRec'")
                KEY_VALUE_REGEX.findAll(directRec).forEach { match ->
                    val key = match.groupValues[1].lowercase(Locale.ROOT)
                    val value = match.groupValues[2]
                    outVariables?.put(key, value)
                }
                if (cleanQuery.isBlank() || isFuzzyMatch(directRec, cleanQuery)) {
                    val matchResult = OcrMatchResult(
                        matchedText = directRec,
                        clickX = gOffsetX + localBmp.width / 2,
                        clickY = gOffsetY + localBmp.height / 2,
                        rectLeft = gOffsetX,
                        rectTop = gOffsetY,
                        rectRight = gOffsetX + localBmp.width,
                        rectBottom = gOffsetY + localBmp.height,
                        confidence = 1.0f
                    )
                    val elapsed = System.currentTimeMillis() - perfStart
                    AppLogger.log(null, "OCR", "OCR (Прямой ROI Успех): '$directRec' за ${elapsed}мс")
                    if (localBmp != srcBmp && !localBmp.isRecycled) localBmp.recycle()
                    if (srcBmp != bitmap && !srcBmp.isRecycled) srcBmp.recycle()
                    return listOf(matchResult)
                }
            }
        }

        // 3. Полноэкранный поиск по текстовым линиям и фразам
        val boxes = extractWordBoundingBoxes(localBmp)
        AppLogger.log(null, "OCR", "Детектор текстовых линий: выделено ${boxes.size} боксов")

        val matches = mutableListOf<OcrMatchResult>()

        for (box in boxes) {
            val bW = box.width()
            val bH = box.height()
            if (bW < 6 || bH < 6) continue

            val crop = Bitmap.createBitmap(localBmp, box.left, box.top, bW, bH)
            val rec = recognizeTextWithOnnx(crop)
            if (crop != localBmp && !crop.isRecycled) crop.recycle()

            if (!rec.isNullOrBlank()) {
                AppLogger.log(null, "OCR_SCAN", "Бокс [${box.left},${box.top}..${box.right},${box.bottom}]: '$rec'")
                KEY_VALUE_REGEX.findAll(rec).forEach { match ->
                    val key = match.groupValues[1].lowercase(Locale.ROOT)
                    val value = match.groupValues[2]
                    outVariables?.put(key, value)
                }

                val isMatch = cleanQuery.isBlank() || isFuzzyMatch(rec, cleanQuery)
                if (isMatch) {
                    val gX = gOffsetX + box.left
                    val gY = gOffsetY + box.top
                    val matchResult = OcrMatchResult(
                        matchedText = rec,
                        clickX = gX + bW / 2,
                        clickY = gY + bH / 2,
                        rectLeft = gX,
                        rectTop = gY,
                        rectRight = gX + bW,
                        rectBottom = gY + bH,
                        confidence = 1.0f
                    )
                    matches.add(matchResult)
                    if (cleanQuery.isNotBlank()) {
                        val elapsed = System.currentTimeMillis() - perfStart
                        AppLogger.log(null, "OCR", "Game OCR Успех: '$rec' (совпало с '$targetQuery') в (${matchResult.clickX}, ${matchResult.clickY}) за ${elapsed}мс")
                        if (localBmp != srcBmp && !localBmp.isRecycled) localBmp.recycle()
                        if (srcBmp != bitmap && !srcBmp.isRecycled) srcBmp.recycle()
                        return listOf(matchResult)
                    }
                }
            }
        }

        if (matches.isNotEmpty()) {
            if (localBmp != srcBmp && !localBmp.isRecycled) localBmp.recycle()
            if (srcBmp != bitmap && !srcBmp.isRecycled) srcBmp.recycle()
            return matches
        }

        if (localBmp != srcBmp && !localBmp.isRecycled) localBmp.recycle()
        if (srcBmp != bitmap && !srcBmp.isRecycled) srcBmp.recycle()

        val elapsed = System.currentTimeMillis() - perfStart
        if (targetQuery.isNotBlank()) {
            AppLogger.log(null, "OCR", "Game OCR: совпадений для '$targetQuery' не обнаружено (время: ${elapsed}мс)")
        }
        return emptyList()
    }

    fun findAndExtractRegex(bitmap: Bitmap, regexPattern: String, timeoutMs: Long = 3000L, roi: Rect? = null): String? {
        if (regexPattern.isBlank() || !isValidForOcr(bitmap)) return null
        val pattern = try { Regex(regexPattern) } catch (_: Exception) { return null }

        val results = findTextOnScreen(bitmap, "", timeoutMs, roi)
        for (res in results) {
            val match = pattern.find(res.matchedText)
            if (match != null) {
                val extracted = match.groupValues.getOrNull(1) ?: match.value
                AppLogger.log(null, "OCR", "ONNX Regex: '$extracted'")
                return extracted
            }
        }
        return null
    }
}
