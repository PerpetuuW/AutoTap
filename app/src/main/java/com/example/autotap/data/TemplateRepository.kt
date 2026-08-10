package com.example.autotap.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import com.example.autotap.engine.ai.CalibratedMask
import com.example.autotap.engine.ai.MaskCalibrator
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import org.json.JSONObject
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import kotlin.math.abs

class TemplateRepository(private val context: Context) {

    private val bitmapCache = ConcurrentHashMap<Int, Bitmap>()
    private val calibratedMaskCache = ConcurrentHashMap<Int, CalibratedMask>()
    private val calibrator = MaskCalibrator()

    fun getNextFreeTemplateIndex(): Int {
        var index = 0
        while (File(context.filesDir, "template_$index.png").exists()) {
            index++
        }
        return index
    }

    fun getLatestAvailableTemplateIndex(): Int {
        val files = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") }
        if (files.isNullOrEmpty()) return 0
        return files.mapNotNull { file ->
            file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull()
        }.maxOrNull() ?: 0
    }

    fun saveTemplate(index: Int, bitmap: Bitmap): Boolean {
        return try {
            val file = File(context.filesDir, "template_$index.png")
            file.outputStream().use { out ->
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
            }

            val metrics = context.resources.displayMetrics
            val metaObj = JSONObject().apply {
                put("sourceWidth", metrics.widthPixels)
                put("sourceHeight", metrics.heightPixels)
                put("sourceDpi", metrics.densityDpi)
            }
            File(context.filesDir, "template_${index}_meta.json").writeText(metaObj.toString())

            bitmapCache[index] = bitmap

            val calibrated = calibrator.calibrate(bitmap)
            calibratedMaskCache[index] = calibrated

            logDiagnostic("AI_SCANNER", "Маска #$index сохранена с метаданными экрана (${metrics.widthPixels}x${metrics.heightPixels}, ${metrics.densityDpi} DPI).")
            true
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка сохранения и калибровки маски $index", e)
            false
        }
    }

    fun loadTemplate(index: Int): Bitmap? {
        val cached = bitmapCache[index]
        if (cached != null && !cached.isRecycled) {
            return cached
        }
        return try {
            var file = File(context.filesDir, "template_$index.png")
            var targetIndex = index

            // Авто-фолбэк на имеющуюся маску, если запрошенный файл отсутствует
            if (!file.exists()) {
                val fallbackIndex = getLatestAvailableTemplateIndex()
                file = File(context.filesDir, "template_$fallbackIndex.png")
                targetIndex = fallbackIndex
                logDiagnostic("AI_SCANNER", "Маска $index не найдена. Выполнен авто-фолбэк на имеющуюся маску #$fallbackIndex")
            }

            if (!file.exists()) return null
            val rawBitmap = BitmapFactory.decodeFile(file.absolutePath) ?: return null

            val metrics = context.resources.displayMetrics
            val metaFile = File(context.filesDir, "template_${targetIndex}_meta.json")

            val finalBitmap = if (metaFile.exists()) {
                try {
                    val metaJson = JSONObject(metaFile.readText())
                    val srcW = metaJson.optInt("sourceWidth", metrics.widthPixels)
                    val srcH = metaJson.optInt("sourceHeight", metrics.heightPixels)

                    val scaleX = metrics.widthPixels.toFloat() / srcW.coerceAtLeast(1)
                    val scaleY = metrics.heightPixels.toFloat() / srcH.coerceAtLeast(1)
                    val avgScale = (scaleX + scaleY) / 2f

                    if (abs(avgScale - 1.0f) > 0.04f) {
                        val targetW = (rawBitmap.width * avgScale).toInt().coerceAtLeast(4)
                        val targetH = (rawBitmap.height * avgScale).toInt().coerceAtLeast(4)
                        Bitmap.createScaledBitmap(rawBitmap, targetW, targetH, true)
                    } else rawBitmap
                } catch (_: Exception) { rawBitmap }
            } else rawBitmap

            bitmapCache[targetIndex] = finalBitmap
            val calibrated = calibrator.calibrate(finalBitmap)
            calibratedMaskCache[targetIndex] = calibrated
            finalBitmap
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка загрузки маски $index", e)
            null
        }
    }

    fun loadCalibratedMask(index: Int): CalibratedMask? {
        val cached = calibratedMaskCache[index]
        if (cached != null && !cached.original.isRecycled) {
            return cached
        }
        val bitmap = loadTemplate(index) ?: return null
        val calibrated = calibrator.calibrate(bitmap)
        calibratedMaskCache[index] = calibrated
        return calibrated
    }

    fun recalibrateTemplate(index: Int): CalibratedMask? {
        val bitmap = loadTemplate(index) ?: return null
        val calibrated = calibrator.calibrate(bitmap)
        calibratedMaskCache[index] = calibrated
        logDiagnostic("AI_SCANNER", "Принудительная калибровка маски #$index успешно выполнена.")
        return calibrated
    }

    fun moveTemplateToTrash(index: Int): Boolean {
        return try {
            val file = File(context.filesDir, "template_$index.png")
            if (file.exists()) {
                val trashDir = File(context.filesDir, "trash")
                trashDir.mkdirs()
                val trashFile = File(trashDir, "template_$index.png")
                file.renameTo(trashFile)

                File(context.filesDir, "template_${index}_meta.json").delete()

                bitmapCache.remove(index)
                calibratedMaskCache.remove(index)

                logDiagnostic("AI_SCANNER", "Маска #$index перемещена в корзину.")
                true
            } else false
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка перемещения маски $index в корзину", e)
            false
        }
    }

    fun restoreTemplateFromTrash(index: Int): Boolean {
        return try {
            val trashFile = File(File(context.filesDir, "trash"), "template_$index.png")
            if (trashFile.exists()) {
                val targetFile = File(context.filesDir, "template_$index.png")
                trashFile.renameTo(targetFile)
                loadTemplate(index)
                logDiagnostic("AI_SCANNER", "Маска #$index восстановлена из корзины.")
                true
            } else false
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка восстановления маски $index из корзины", e)
            false
        }
    }
}
