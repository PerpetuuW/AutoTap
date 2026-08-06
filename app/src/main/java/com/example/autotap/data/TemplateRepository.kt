package com.example.autotap.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import com.example.autotap.engine.ai.CalibratedMask
import com.example.autotap.engine.ai.MaskCalibrator
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import java.io.File

class TemplateRepository(private val context: Context) {

    private val bitmapCache = mutableMapOf<Int, Bitmap>()
    private val calibratedMaskCache = mutableMapOf<Int, CalibratedMask>()
    private val calibrator = MaskCalibrator()

    fun getNextFreeTemplateIndex(): Int {
        var index = 0
        while (File(context.filesDir, "template_$index.png").exists()) {
            index++
        }
        return index
    }

    fun saveTemplate(index: Int, bitmap: Bitmap): Boolean {
        return try {
            val file = File(context.filesDir, "template_$index.png")
            file.outputStream().use { out ->
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
            }
            bitmapCache[index] = bitmap

            val calibrated = calibrator.calibrate(bitmap)
            calibratedMaskCache[index] = calibrated

            logDiagnostic("AI_SCANNER", "Маска #$index успешно сохранена и калибрована (контур: ${calibrated.contour.size} точек, BBox: ${calibrated.boundingBox}).")
            true
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка сохранения и калибровки маски $index", e)
            false
        }
    }

    fun loadTemplate(index: Int): Bitmap? {
        if (bitmapCache.containsKey(index)) {
            val cached = bitmapCache[index]
            if (cached != null && !cached.isRecycled) {
                return cached
            }
        }
        return try {
            val file = File(context.filesDir, "template_$index.png")
            if (!file.exists()) {
                logDiagnostic("AI_SCANNER", "Маска $index не найдена на диске.")
                return null
            }
            val bitmap = BitmapFactory.decodeFile(file.absolutePath)
            if (bitmap != null) {
                bitmapCache[index] = bitmap
                val calibrated = calibrator.calibrate(bitmap)
                calibratedMaskCache[index] = calibrated
                logDiagnostic("AI_SCANNER", "Маска $index загружена с диска и откалибрована.")
            }
            bitmap
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка загрузки маски $index", e)
            null
        }
    }

    fun loadCalibratedMask(index: Int): CalibratedMask? {
        if (calibratedMaskCache.containsKey(index)) {
            val cached = calibratedMaskCache[index]
            if (cached != null && !cached.original.isRecycled) {
                return cached
            }
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

                // Очистка памяти Bitmap для утилизации ОЗУ
                bitmapCache.remove(index)?.recycle()
                calibratedMaskCache.remove(index)

                logDiagnostic("AI_SCANNER", "Маска #$index перемещена в корзину с высвобождением ОЗУ.")
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
