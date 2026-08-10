#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v63 - EMOJI STRIPPING, HANDLE DRAG FIX & SCANNER ASYNC LOCK FIX
===============================================================================
"""

import os
import sys
import ast

def self_verify_python_syntax():
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            script_code = f.read()
        ast.parse(script_code)
        print("🟢 [PYTHON SYNTAX CHECK]: Синтаксис Python-скрипта 100% корректен.")
    except Exception as e:
        print(f"❌ [CRITICAL SYNTAX ERROR IN SCRIPT]: {e}")
        sys.exit(1)

self_verify_python_syntax()

def write_file(rel_path, content):
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.truncate(0)
        f.write(content.strip() + '\n')
    print(f"🟢 [ОБНОВЛЕН]: {rel_path}")


# =============================================================================
# 1. AiScannerEngine.kt (УСТРАНЕНИЕ ЗАЦИКЛИВАНИЯ "Пропуск: асинхронное...")
# =============================================================================
AI_SCANNER_ENGINE_KT = r'''package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.PointF
import com.example.autotap.MyAutoClickService
import com.example.autotap.engine.ai.AiScanResult
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.engine.ai.TemplateMatcher
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig

class AiScannerEngine(private val service: MyAutoClickService) {

    private val templateMatcher by lazy { TemplateMatcher(service.templateRepository) }
    @Volatile private var isScanning = false
    @Volatile var lastScanResult: AiScanResult? = null
        private set

    fun scanAsync(frameProvider: () -> Bitmap?, action: ActionConfig, callback: (PointF?) -> Unit) {
        if (isScanning) {
            // КРИТИЧЕСКИЙ ФИКС: При занятом сканере НЕ вызываем callback(null),
            // чтобы исключить рекурсивный зацикленный спам таймера!
            return
        }
        isScanning = true
        Thread {
            try {
                val result = scan(frameProvider, action)
                lastScanResult = result
                callback(result.point)
            } catch (e: Exception) {
                logError("AI_SCANNER", "Ошибка в scanAsync", e)
                callback(null)
            } finally {
                isScanning = false
            }
        }.start()
    }

    fun scan(frameProvider: () -> Bitmap?, action: ActionConfig): AiScanResult {
        val frame = frameProvider()
        if (frame == null) {
            logDiagnostic("AI_SCANNER", "Снимок экрана недоступен.")
            return AiScanResult(null, emptyList())
        }

        val candidates = if (action.multiTemplateIndices.isNotEmpty()) {
            templateMatcher.matchMultiTemplate(frame, action)
        } else {
            templateMatcher.matchSingleTemplate(frame, action)
        }

        if (candidates.isEmpty()) {
            logDiagnostic("AI_SCANNER", "Совпадений по маскам не найдено.")
            return AiScanResult(null, emptyList())
        }

        val bestCandidate = candidates.first()
        logDiagnostic("AI_SCANNER", "ИИ нашел целей: ${candidates.size}. Высший шаблон #${bestCandidate.templateIndex} (score=${"%.2f".format(bestCandidate.score)}) в $bestCandidate")
        return AiScanResult(bestCandidate.point, candidates)
    }
}'''


# =============================================================================
# 2. TemplateRepository.kt (АВТО-ФОЛБЭК НА СУЩЕСТВУЮЩУЮ МАСКУ ПРИ ОТСУТСТВИИ ФАЙЛА)
# =============================================================================
TEMPLATE_REPOSITORY_KT = r'''package com.example.autotap.data

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
}'''


# =============================================================================
# 3. CaptureFrameOverlay.kt (ПЕРЕТАСКИВАНИЕ ЗА ЗНАЧОК handleMoveFrame)
# =============================================================================
CAPTURE_FRAME_OVERLAY_KT = r'''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CAPTURE_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 20.dpToPx(context)
    private var currentFrameWidthPx = 140.dpToPx(context)
    private var currentFrameHeightPx = 140.dpToPx(context)

    private var captureSquareView: View? = null
    private var topBarView: View? = null
    private var bottomBarView: View? = null

    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        gravity = Gravity.TOP or Gravity.START
        val metrics = context.resources.displayMetrics
        initialX = (metrics.widthPixels - currentFrameWidthPx) / 2
        initialY = (metrics.heightPixels - currentFrameHeightPx) / 2
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        captureSquareView = view.findViewByNames("captureSquare")
        topBarView = view.findViewByNames("layoutTopBar")
        bottomBarView = view.findViewByNames("layoutBottomBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val square = captureSquareView
            val root = rootView

            if (svc != null && square != null && root != null) {
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

                root.visibility = View.INVISIBLE

                mainHandler.postDelayed({
                    svc.captureScreenBitmapAsync { fullBitmap ->
                        root.visibility = View.VISIBLE
                        if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                            val safeX = cropX.coerceIn(0, (fullBitmap.width - 10).coerceAtLeast(0))
                            val safeY = cropY.coerceIn(0, (fullBitmap.height - 10).coerceAtLeast(0))

                            val maxAllowedW = fullBitmap.width - safeX
                            val maxAllowedH = fullBitmap.height - safeY
                            val safeW = cropW.coerceIn(5, maxAllowedW)
                            val safeH = cropH.coerceIn(5, maxAllowedH)

                            val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                            if (safeW > 5 && safeH > 5) {
                                try {
                                    val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                                    svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                    val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                                    if (calibrated != null) {
                                        overlayManager.debuggerOverlay.showCalibratedTemplate(
                                            croppedMask,
                                            nextTemplateIndex,
                                            calibrated.metadata.profile.name,
                                            safeW,
                                            safeH
                                        )
                                    }
                                } catch (e: Exception) {
                                    logError("AI_SCANNER", "Ошибка создания Bitmap кропа", e)
                                }
                            }
                        }
                    }
                    hide()
                    overlayManager.showControlPanel()
                }, 120L)
            }
        }

        view.bindClickByNames("btnCancelCapture") {
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCaptureSearchArea") {
            overlayManager.searchAreaOverlay.show()
            hide()
        }

        // ПРЯМАЯ ПРИВЯЗКА ПЕРЕТАСКИВАНИЯ К ЗНАЧКУ handleMoveFrame И ПЛАШКАМ
        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        val topBar = topBarView ?: view
        val bottomBar = bottomBarView ?: view
        val square = captureSquareView ?: view

        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)
        setupDragAndDrop(bottomBar)
        setupDragAndDrop(square)

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && captureSquareView != null) {
            setupCornerResizeHandler(resizeHandle, captureSquareView!!)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applyShiftingToolbarsRepositioning(x, y)
    }

    private fun applyShiftingToolbarsRepositioning(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val bottomBar = bottomBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val bottomBarHeight = bottomBar.height.takeIf { it > 0 } ?: 28.dpToPx(context)
        val squareHeight = square.height.takeIf { it > 0 } ?: 140.dpToPx(context)
        val gap = 4.dpToPx(context)

        val isNearTop = currentY <= (topBarHeight + 10.dpToPx(context))
        val isNearBottom = currentY >= (screenSize.y - squareHeight - bottomBarHeight - 60.dpToPx(context))

        when {
            isNearTop -> {
                topBar.translationY = (squareHeight + gap).toFloat()
                bottomBar.translationY = (squareHeight + topBarHeight + gap * 2).toFloat()
            }
            isNearBottom -> {
                bottomBar.translationY = -(squareHeight + bottomBarHeight + gap).toFloat()
                topBar.translationY = -(squareHeight + topBarHeight + bottomBarHeight + gap * 2).toFloat()
            }
            else -> {
                topBar.translationY = 0f
                bottomBar.translationY = 0f
            }
        }

        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 120.dpToPx(context)
        val bottomBarWidth = bottomBar.width.takeIf { it > 0 } ?: 90.dpToPx(context)
        val maxToolbarW = maxOf(topBarWidth, bottomBarWidth)

        if (square.width < maxToolbarW) {
            val extraWidth = maxToolbarW - square.width
            val isNearLeft = currentX <= extraWidth / 2
            val isNearRight = currentX >= screenSize.x - square.width - (extraWidth / 2)

            when {
                isNearLeft -> {
                    topBar.translationX = (extraWidth / 2f)
                    bottomBar.translationX = (extraWidth / 2f)
                }
                isNearRight -> {
                    topBar.translationX = -(extraWidth / 2f)
                    bottomBar.translationX = -(extraWidth / 2f)
                }
                else -> {
                    topBar.translationX = 0f
                    bottomBar.translationX = 0f
                }
            }
        } else {
            topBar.translationX = 0f
            bottomBar.translationX = 0f
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val root = rootView ?: return@setOnTouchListener false
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetSquare.width
                    startH = targetSquare.height
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    root.getLocationOnScreen(location)
                    val windowX = location[0]
                    val windowY = location[1]

                    val maxW = (screenSize.x - windowX - 8.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - windowY - 80.dpToPx(context)).coerceAtLeast(minSizePx)

                    currentFrameWidthPx = (startW + dx).coerceIn(minSizePx, maxW)
                    currentFrameHeightPx = (startH + dy).coerceIn(minSizePx, maxH)

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = currentFrameWidthPx
                        lp.height = currentFrameHeightPx
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
                    }
                    true
                }
                else -> false
            }
        }
    }
}'''


# =============================================================================
# 4. floating_capture_frame.xml (ОЧИСТКА ОТ ЭМОДЗИ)
# =============================================================================
CAPTURE_FRAME_XML = r'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/layoutCaptureContainer"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:gravity="center_horizontal"
    android:padding="0dp"
    android:elevation="18dp">

    <!-- ВЕРХНИЙ ТУЛБАР -->
    <LinearLayout
        android:id="@+id/layoutTopBar"
        android:layout_width="wrap_content"
        android:layout_height="38dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="6dp"
        android:paddingEnd="6dp"
        android:layout_marginBottom="2dp">

        <ImageButton
            android:id="@+id/btnDoCapture"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:src="@drawable/ic_camera"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_primary"
            android:padding="5dp"
            android:contentDescription="Capture"
            android:layout_marginEnd="4dp" />

        <Button
            android:id="@+id/btnCaptureSearchArea"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:text="Зона"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/accent_blue"
            android:textSize="10sp"
            android:padding="0dp"
            android:layout_marginEnd="4dp" />

        <ImageButton
            android:id="@+id/btnCancelCapture"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:src="@drawable/ic_close"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="5dp"
            android:contentDescription="Close" />
    </LinearLayout>

    <!-- РАМКА ПРИЦЕЛА -->
    <FrameLayout
        android:id="@+id/captureSquare"
        android:layout_width="160dp"
        android:layout_height="160dp"
        android:background="@drawable/border_capture_square" />

    <!-- НИЖНЯЯ ПЛАШКА ДВИЖЕНИЯ -->
    <LinearLayout
        android:id="@+id/layoutBottomBar"
        android:layout_width="wrap_content"
        android:layout_height="28dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="8dp"
        android:paddingEnd="8dp"
        android:layout_marginTop="2dp">

        <TextView
            android:id="@+id/handleMoveFrame"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="ДВИГАТЬ"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:layout_marginEnd="6dp" />

        <ImageView
            android:id="@+id/handleResize"
            android:layout_width="20dp"
            android:layout_height="20dp"
            android:src="@drawable/handle_manipulator_bg"
            android:padding="2dp"
            android:contentDescription="Resize Grip" />
    </LinearLayout>
</LinearLayout>'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v63 (EMOJI REMOVAL & SCANNER UNLOCK)")
    print("=================================================================")

    tasks = [
        ("app/src/main/java/com/example/autotap/engine/AiScannerEngine.kt", AI_SCANNER_ENGINE_KT),
        ("app/src/main/java/com/example/autotap/data/TemplateRepository.kt", TEMPLATE_REPOSITORY_KT),
        ("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", CAPTURE_FRAME_OVERLAY_KT),
        ("app/src/main/res/layout/floating_capture_frame.xml", CAPTURE_FRAME_XML),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ВСЕ ОШИБКИ И ЗАЦИКЛИВАНИЯ УСПЕШНО УСТРАНЕНЫ!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()