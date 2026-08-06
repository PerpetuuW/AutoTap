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

    fun saveTemplate(index: Int, bitmap: Bitmap): Boolean {
        return try {
            val file = File(context.filesDir, "template_$index.png")
            file.outputStream().use { out ->
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
            }
            bitmapCache[index] = bitmap

            // Автоматическая калибровка умной маски сразу при создании!
            val calibrated = calibrator.calibrate(bitmap)
            calibratedMaskCache[index] = calibrated

            logDiagnostic("AI_SCANNER", "Маска #$index успешно сохранена и автоматически откалибрована (контур: ${calibrated.contour.size} точек, BBox: ${calibrated.boundingBox}).")
            true
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка сохранения и калибровки маски $index", e)
            false
        }
    }

    fun loadTemplate(index: Int): Bitmap? {
        if (bitmapCache.containsKey(index)) {
            return bitmapCache[index]
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
                logDiagnostic("AI_SCANNER", "Маска $index успешно загружена с диска и откалибрована.")
            }
            bitmap
        } catch (e: Exception) {
            logError("AI_SCANNER", "Ошибка загрузки маски $index", e)
            null
        }
    }

    fun loadCalibratedMask(index: Int): CalibratedMask? {
        if (calibratedMaskCache.containsKey(index)) {
            return calibratedMaskCache[index]
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
        logDiagnostic("AI_SCANNER", "Принудительная ручная калибровка маски #$index успешно выполнена.")
        return calibrated
    }
}
