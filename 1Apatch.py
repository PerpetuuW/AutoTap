#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v67 - ASYNC CALIBRATION THREADING & UNIFIED TOP TOOLBAR FIX
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
# 1. FLOATING CAPTURE FRAME (Е Д И Н Ы Й  Т У Л Б А Р)
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

    <!-- ЕДИНЫЙ ОБЪЕДИНЕННЫЙ ТУЛБАР (Двигать + Камера + Зона + Закрыть в 1 строку) -->
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

        <TextView
            android:id="@+id/handleMoveFrame"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="⁝⁝ ДВИГАТЬ"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:paddingStart="4dp"
            android:paddingEnd="6dp"
            android:layout_marginEnd="4dp" />

        <ImageButton
            android:id="@+id/btnDoCapture"
            android:layout_width="32dp"
            android:layout_height="32dp"
            android:src="@drawable/ic_camera"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_primary"
            android:padding="5dp"
            android:contentDescription="Capture"
            android:layout_marginEnd="4dp" />

        <Button
            android:id="@+id/btnCaptureSearchArea"
            android:layout_width="32dp"
            android:layout_height="32dp"
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
            android:layout_width="32dp"
            android:layout_height="32dp"
            android:src="@drawable/ic_close"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="5dp"
            android:contentDescription="Close" />
    </LinearLayout>

    <!-- 100% ЧИСТЫЙ КАДР С ВЫНЕСЕННОЙ РУЧКОЙ РЕСАЙЗА -->
    <FrameLayout
        android:id="@+id/captureSquare"
        android:layout_width="160dp"
        android:layout_height="160dp"
        android:background="@drawable/border_capture_square">

        <ImageView
            android:id="@+id/handleResize"
            android:layout_width="28dp"
            android:layout_height="28dp"
            android:layout_gravity="bottom|end"
            android:src="@drawable/handle_manipulator_bg"
            android:padding="3dp"
            android:contentDescription="Resize Grip" />
    </FrameLayout>
</LinearLayout>'''


# =============================================================================
# 2. CAPTURE FRAME OVERLAY KOTLIN CLASS
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

                                    overlayManager.debuggerOverlay.showCalibratedTemplate(
                                        croppedMask,
                                        nextTemplateIndex,
                                        "MEDIUM",
                                        safeW,
                                        safeH
                                    )
                                } catch (e: Exception) {
                                    logError("AI_SCANNER", "Ошибка создания Bitmap кропа", e)
                                }
                            }
                        }
                    }
                    hide()
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

        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        val topBar = topBarView ?: view

        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)

        val resizeHandle = view.findViewByNames("handleResize")
        val sq = captureSquareView
        if (resizeHandle != null && sq != null) {
            setupCornerResizeHandler(resizeHandle, sq)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        applySmartEdgeFlipping(x, y)
    }

    private fun applySmartEdgeFlipping(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val gap = 4.dpToPx(context)

        val isNearTop = currentY <= (topBarHeight + 10.dpToPx(context))
        topBar.translationY = if (isNearTop) (square.height + gap).toFloat() else 0f

        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 110.dpToPx(context)
        if (square.width < topBarWidth) {
            val extraWidth = topBarWidth - square.width
            val isNearLeft = currentX <= extraWidth / 2
            val isNearRight = currentX >= screenSize.x - square.width - (extraWidth / 2)

            when {
                isNearLeft -> topBar.translationX = (extraWidth / 2f)
                isNearRight -> topBar.translationX = -(extraWidth / 2f)
                else -> topBar.translationX = 0f
            }
        } else {
            topBar.translationX = 0f
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetSquare.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = targetSquare.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    targetSquare.getLocationOnScreen(location)
                    val squareX = location[0]
                    val squareY = location[1]

                    val maxW = (screenSize.x - squareX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - squareY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (startW + dx).coerceIn(minSizePx, maxW)
                    val newH = (startH + dy).coerceIn(minSizePx, maxH)

                    currentFrameWidthPx = newW
                    currentFrameHeightPx = newH

                    val lp = targetSquare.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetSquare.layoutParams = lp
                        targetSquare.requestLayout()
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    true
                }
                else -> false
            }
        }
    }
}'''


# =============================================================================
# 3. SCENARIO DEBUGGER OVERLAY (ФОНОВЫЙ ПОТОК КАЛИБРОВКИ БЕЗ ЗАВИСАНИЯ UI)
# =============================================================================
SCENARIO_DEBUGGER_OVERLAY_KT = r'''package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Typeface
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.dpToPx
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logAppEvent
import com.example.autotap.model.ActionConfig
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null
    private var ivPreview: ImageView? = null
    private var btnConfirm: Button? = null
    private var btnTrash: Button? = null
    private var currentTemplateIndex = -1

    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        initialY = 90.dpToPx(context)
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundResource(R.drawable.panel_background)
            setPadding(24, 16, 24, 16)

            val tv = TextView(context).apply {
                text = "Калибровка ИИ-Маски"
                setTextColor(Color.parseColor("#00F5D4"))
                textSize = 14f
                setTypeface(null, Typeface.BOLD)
                gravity = Gravity.CENTER
            }
            statusText = tv
            addView(tv)

            val img = ImageView(context).apply {
                visibility = View.GONE
                setPadding(0, 10, 0, 10)
            }
            ivPreview = img
            addView(img, LinearLayout.LayoutParams(120.dpToPx(context), 120.dpToPx(context)))

            val btnRow = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
                setPadding(0, 12, 0, 0)
            }

            btnConfirm = Button(context).apply {
                text = "Подтвердить маску"
                textSize = 11f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#1F6FEB"))
                setTextColor(Color.WHITE)
                setOnClickListener {
                    confirmSmartMaskGeneration()
                }
            }

            btnTrash = Button(context).apply {
                text = "Удалить в корзину"
                textSize = 11f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#2A1215"))
                setTextColor(Color.parseColor("#FF5B5B"))
                setOnClickListener {
                    if (currentTemplateIndex >= 0) {
                        MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(currentTemplateIndex)
                    }
                    overlayManager.candidateOverlay.hide()
                    hide()
                }
            }

            val btnLp = LinearLayout.LayoutParams(0, 44.dpToPx(context), 1.0f)
            btnRow.addView(btnConfirm, btnLp)
            btnRow.addView(View(context), LinearLayout.LayoutParams(10.dpToPx(context), 1))
            btnRow.addView(btnTrash, btnLp)
            addView(btnRow, LinearLayout.LayoutParams(270.dpToPx(context), LinearLayout.LayoutParams.WRAP_CONTENT))
        }

        return root
    }

    // ВЫПОЛНЕНИЕ ПРОБНОГО ПОИСКА В ОТДЕЛЬНОМ ФОНОВОМ ПОТОКЕ (БЕЗ ЗАВИСАНИЯ UI)
    fun startLiveCalibration(templateIndex: Int, directBitmap: Bitmap? = null) {
        this.currentTemplateIndex = templateIndex
        show()

        val svc = MyAutoClickService.instance ?: return
        val bitmap = directBitmap ?: svc.templateRepository.loadTemplate(templateIndex)

        if (bitmap != null) {
            ivPreview?.setImageBitmap(bitmap)
            ivPreview?.visibility = View.VISIBLE
            statusText?.text = "Сканирование экрана для Маски #$templateIndex...\nПоиск объекта на экране..."

            svc.captureScreenBitmapAsync { frameBmp ->
                if (frameBmp != null) {
                    // Тяжелый ИИ-поиск перенесен в фоновый Thread!
                    Thread {
                        val testAction = ActionConfig(selectedTemplateIndex = templateIndex, similarityPercent = 70)
                        val scanResult = svc.aiScannerEngine.scan({ frameBmp }, testAction)
                        val candidates = scanResult.candidates

                        // Возвращаемся на UI-поток для обновления интерфейса
                        mainHandler.post {
                            if (candidates.isNotEmpty()) {
                                val top = candidates.first()
                                val percent = "${(top.score * 100).toInt()}%"
                                statusText?.text = "🎯 Объект найден ($percent)!\nПроверьте маяк и подтвердите маску."
                                overlayManager.candidateOverlay.showRadarBeaconCandidates(candidates) {
                                    confirmSmartMaskGeneration()
                                }
                            } else {
                                statusText?.text = "Пробный поиск: объект пока не найден.\nПодтвердите создание маски #$templateIndex."
                            }
                        }
                    }.start()
                }
            }
        } else {
            statusText?.text = "Ошибка загрузки маски #$templateIndex"
        }
    }

    private fun confirmSmartMaskGeneration() {
        val svc = MyAutoClickService.instance
        if (svc != null && currentTemplateIndex >= 0) {
            val calibrated = svc.templateRepository.recalibrateTemplate(currentTemplateIndex)
            val profile = calibrated?.metadata?.profile?.name ?: "MEDIUM"
            val recSim = calibrated?.metadata?.recommendedSimilarity ?: 85

            Toast.makeText(
                context,
                "Умная маска #$currentTemplateIndex создана! Профиль: $profile (Порог: $recSim%)",
                Toast.LENGTH_LONG
            ).show()
            logAppEvent("AI_SCANNER", "Умная маска #$currentTemplateIndex сгенерирована.")
        }
        overlayManager.candidateOverlay.hide()
        hide()
    }

    fun showCalibratedTemplate(bitmap: Bitmap, templateIndex: Int, profileName: String, widthPx: Int, heightPx: Int) {
        startLiveCalibration(templateIndex, bitmap)
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        if (candidates.isEmpty()) {
            showNoMatch()
            return
        }
        show()
        val topCandidate = candidates.first()
        val scorePercent = "${(topCandidate.score * 100).toInt()}%"
        statusText?.text = "Найден объект: точность $scorePercent\nПодтвердите выбор объекта"
        ivPreview?.visibility = View.GONE
        logAppEvent("AI_SCANNER", "ИИ нашел совпадение: Маска #${topCandidate.templateIndex}, точность: $scorePercent")

        mainHandler.removeCallbacksAndMessages(null)
        mainHandler.postDelayed({ hide() }, 2500L)
    }

    fun showNoMatch() {
        show()
        statusText?.text = "ИИ Поиск: совпадений не найдено"
        ivPreview?.visibility = View.GONE
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")

        mainHandler.removeCallbacksAndMessages(null)
        mainHandler.postDelayed({ hide() }, 2000L)
    }

    override fun hide() {
        mainHandler.removeCallbacksAndMessages(null)
        super.hide()
    }
}'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v67 (BACKGROUND CALIBRATION & UNIFIED BAR)")
    print("=================================================================")

    tasks = [
        ("app/src/main/res/layout/floating_capture_frame.xml", CAPTURE_FRAME_XML),
        ("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", CAPTURE_FRAME_OVERLAY_KT),
        ("app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt", SCENARIO_DEBUGGER_OVERLAY_KT),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ЗАВИСАНИЕ КАЛИБРОВКИ И НАЛОЖЕНИЕ КНОПОК ПОЛНОСТЬЮ ИСПРАВЛЕНЫ!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()