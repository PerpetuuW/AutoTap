#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ast

# -----------------------------------------------------------------------------
# 1. PYTHON SELF-SYNTAX VALIDATOR GUARD (ast.parse)
# -----------------------------------------------------------------------------
def validate_python_self_syntax():
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print("[✓] AST Self-Syntax Validation: Python code syntax is valid.")
    except Exception as e:
        print(f"[💥] CRITICAL PYTHON SYNTAX ERROR in patch script: {e}")
        sys.exit(1)

validate_python_self_syntax()

# -----------------------------------------------------------------------------
# 2. DEFINITIONS OF UPDATED FILES (V58 EXTERNAL RESIZE & 4 SIDE MANIPULATORS)
# -----------------------------------------------------------------------------

FILES_TO_PATCH = {}

# FILE 1: floating_capture_frame.xml (Outer Resize Handle & 4 Side Drag Handles)
FILES_TO_PATCH["app/src/main/res/layout/floating_capture_frame.xml"] = '''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/layoutCaptureContainer"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:clipChildren="false"
    android:clipToPadding="false">

    <!-- 1. ПЛАВАЮЩАЯ ПАНЕЛЬ КНОПЕК (АВТОНОМНАЯ) -->
    <LinearLayout
        android:id="@+id/layoutTopBar"
        android:layout_width="wrap_content"
        android:layout_height="40dp"
        android:layout_gravity="top|center_horizontal"
        android:layout_marginTop="20dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="8dp"
        android:paddingEnd="8dp"
        android:elevation="24dp">

        <TextView
            android:id="@+id/handleMoveFrame"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="⁝⁝ ПАНЕЛЬ"
            android:textColor="#FFB703"
            android:textSize="11sp"
            android:textStyle="bold"
            android:paddingStart="4dp"
            android:paddingEnd="8dp"
            android:layout_marginEnd="6dp" />

        <ImageButton
            android:id="@+id/btnDoCapture"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:src="@drawable/ic_camera"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_primary"
            android:padding="6dp"
            android:contentDescription="Capture"
            android:layout_marginEnd="6dp" />

        <Button
            android:id="@+id/btnCaptureSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="34dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:text="Зона"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/accent_blue"
            android:textSize="11sp"
            android:textStyle="bold"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:layout_marginEnd="6dp" />

        <ImageButton
            android:id="@+id/btnCancelCapture"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:src="@drawable/ic_close"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="6dp"
            android:contentDescription="Close" />
    </LinearLayout>

    <!-- 2. РАМКА С ВЫНЕСЕННЫМ РЕСАЙЗОМ И 4 МАНИПУЛЯТОРАМИ ПО СТОРОНАМ -->
    <RelativeLayout
        android:id="@+id/layoutFrameWithHandles"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_gravity="center"
        android:clipChildren="false"
        android:clipToPadding="false"
        android:elevation="16dp">

        <!-- ОСНОВНОЕ ПОЛЕ ВЫРЕЗАНИЯ (100% ЧИСТОЕ ВНУТРИ) -->
        <FrameLayout
            android:id="@+id/captureSquare"
            android:layout_width="160dp"
            android:layout_height="160dp"
            android:layout_marginTop="16dp"
            android:layout_marginBottom="16dp"
            android:layout_marginStart="16dp"
            android:layout_marginEnd="16dp"
            android:background="@drawable/border_capture_square" />

        <!-- 1. МАНИПУЛЯТОР ВЕРХНИЙ (СЕРЕДИНА ВЕРХНЕГО КРАЯ) -->
        <TextView
            android:id="@+id/handleMoveTop"
            android:layout_width="36dp"
            android:layout_height="18dp"
            android:layout_alignTop="@id/captureSquare"
            android:layout_centerHorizontal="true"
            android:layout_marginTop="-9dp"
            android:gravity="center"
            android:text="•••"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <!-- 2. МАНИПУЛЯТОР НИЖНИЙ (СЕРЕДИНА НИЖНЕГО КРАЯ) -->
        <TextView
            android:id="@+id/handleMoveBottom"
            android:layout_width="36dp"
            android:layout_height="18dp"
            android:layout_alignBottom="@id/captureSquare"
            android:layout_centerHorizontal="true"
            android:layout_marginBottom="-9dp"
            android:gravity="center"
            android:text="•••"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <!-- 3. МАНИПУЛЯТОР ЛЕВЫЙ (СЕРЕДИНА ЛЕВОГО КРАЯ) -->
        <TextView
            android:id="@+id/handleMoveLeft"
            android:layout_width="18dp"
            android:layout_height="36dp"
            android:layout_alignLeft="@id/captureSquare"
            android:layout_centerVertical="true"
            android:layout_marginLeft="-9dp"
            android:gravity="center"
            android:text=":\n:"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <!-- 4. МАНИПУЛЯТОР ПРАВЫЙ (СЕРЕДИНА ПРАВОГО КРАЯ) -->
        <TextView
            android:id="@+id/handleMoveRight"
            android:layout_width="18dp"
            android:layout_height="36dp"
            android:layout_alignRight="@id/captureSquare"
            android:layout_centerVertical="true"
            android:layout_marginRight="-9dp"
            android:gravity="center"
            android:text=":\n:"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <!-- 5. МАНИПУЛЯТОР РЕСАЙЗА СНИЗУ-СПРАВА (ПОЛНОСТЬЮ ВЫНЕСЕН ЗА ПРЕДЕЛЫ ПОЛЯ!) -->
        <ImageView
            android:id="@+id/handleResize"
            android:layout_width="36dp"
            android:layout_height="36dp"
            android:layout_below="@id/captureSquare"
            android:layout_toEndOf="@id/captureSquare"
            android:layout_marginTop="-12dp"
            android:layout_marginStart="-12dp"
            android:src="@drawable/handle_manipulator_bg"
            android:padding="4dp"
            android:elevation="22dp"
            android:contentDescription="Resize Grip" />
    </RelativeLayout>
</FrameLayout>
'''

# FILE 2: CaptureFrameOverlay.kt (Binding All 4 Side Manipulators & External Resize)
FILES_TO_PATCH["app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt"] = '''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.abs

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CAPTURE_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 30.dpToPx(context)
    private var currentFrameWidthPx = 160.dpToPx(context)
    private var currentFrameHeightPx = 160.dpToPx(context)

    private var captureSquareView: View? = null
    private var topBarView: View? = null

    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        captureSquareView = view.findViewByNames("captureSquare")
        topBarView = view.findViewByNames("layoutTopBar")

        view.bindClickByNames("btnDoCapture", "btn_do_capture") {
            StructuredLogger.logDiagnostic("CAPTURE_FRAME", "Нажата кнопка Снятия Шаблона.")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val square = captureSquareView

            if (svc != null && square != null) {
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

                val screenSize = context.getRealScreenSize()
                val cropNormX = ((cropX + cropW / 2f) / screenSize.x.toFloat()).coerceIn(0f, 1f)
                val cropNormY = ((cropY + cropH / 2f) / screenSize.y.toFloat()).coerceIn(0f, 1f)

                overlayManager.captureCleanScreen(svc) { fullBitmap ->
                    if (fullBitmap != null && fullBitmap.width > 10 && fullBitmap.height > 10) {
                        val realMetrics = context.resources.displayMetrics
                        val scaleX = fullBitmap.width.toFloat() / realMetrics.widthPixels.toFloat()
                        val scaleY = fullBitmap.height.toFloat() / realMetrics.heightPixels.toFloat()

                        val realCropX = (cropX * scaleX).toInt().coerceIn(0, fullBitmap.width - 1)
                        val realCropY = (cropY * scaleY).toInt().coerceIn(0, fullBitmap.height - 1)
                        val realCropW = (cropW * scaleX).toInt().coerceIn(10, (fullBitmap.width - realCropX).coerceAtLeast(10))
                        val realCropH = (cropH * scaleY).toInt().coerceIn(10, (fullBitmap.height - realCropY).coerceAtLeast(10))

                        val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                        if (safeW > 5 && safeH > 5) {
                            try {
                                val croppedMask = Bitmap.createBitmap(fullBitmap, realCropX, realCropY, realCropW, realCropH)
                                val saved = svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)

                                if (saved && svc.actionsList.isNotEmpty()) {
                                    val lastAction = svc.actionsList.last()
                                    lastAction.xNorm = cropNormX
                                    lastAction.yNorm = cropNormY
                                    lastAction.selectedTemplateIndex = nextTemplateIndex
                                }

                                overlayManager.debuggerOverlay.showCalibratedTemplate(
                                    croppedMask,
                                    nextTemplateIndex,
                                    "MEDIUM",
                                    realCropW,
                                    realCropH,
                                    fullBitmap
                                )
                            } catch (e: Exception) {
                                StructuredLogger.logError("CAPTURE_FRAME", "Ошибка создания Bitmap кропа маски", e)
                            }
                        }
                    } else {
                        StructuredLogger.logError("CAPTURE_FRAME", "Скриншот вернул NULL!", null)
                    }
                }
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

        // 💥 НАСТРОЙКА ПРАВИЛЬНЫХ МАНИПУЛЯТОРОВ И ХОЛСТА
        val topBar = topBarView
        if (topBar != null) {
            setupIndependentViewDrag(topBar)
        }

        val frameContainer = view.findViewByNames("layoutFrameWithHandles") ?: captureSquareView
        val sq = captureSquareView

        if (frameContainer != null) {
            setupIndependentViewDrag(frameContainer)
        }

        // 💥 ПРИВЯЗКА ВСЕХ 4 МАНИПУЛЯТОРОВ ПЕРЕМЕЩЕНИЯ ПО СТОРОНАМ
        val hTop = view.findViewByNames("handleMoveTop")
        val hBottom = view.findViewByNames("handleMoveBottom")
        val hLeft = view.findViewByNames("handleMoveLeft")
        val hRight = view.findViewByNames("handleMoveRight")

        if (frameContainer != null) {
            hTop?.let { setupIndependentViewDrag(hTop, frameContainer) }
            hBottom?.let { setupIndependentViewDrag(hBottom, frameContainer) }
            hLeft?.let { setupIndependentViewDrag(hLeft, frameContainer) }
            hRight?.let { setupIndependentViewDrag(hRight, frameContainer) }
        }

        // 💥 ВЫНЕСЕННЫЙ РЕСАЙЗ СНИЗУ-СПРАВА
        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && sq != null) {
            setupCornerResizeHandler(resizeHandle, sq)
        }

        return view
    }

    private fun setupIndependentViewDrag(touchView: View, targetViewToDrag: View = touchView) {
        var startTouchX = 0f
        var startTouchY = 0f
        var initialTranslationX = 0f
        var initialTranslationY = 0f

        touchView.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startTouchX = event.rawX
                    startTouchY = event.rawY
                    initialTranslationX = targetViewToDrag.translationX
                    initialTranslationY = targetViewToDrag.translationY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - startTouchX
                    val dy = event.rawY - startTouchY

                    targetViewToDrag.translationX = initialTranslationX + dx
                    targetViewToDrag.translationY = initialTranslationY + dy
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    true
                }
                else -> false
            }
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetSquare: View) {
        var lastTouchX = 0f
        var lastTouchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    lastTouchX = event.rawX
                    lastTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - lastTouchX).toInt()
                    val dy = (event.rawY - lastTouchY).toInt()

                    lastTouchX = event.rawX
                    lastTouchY = event.rawY

                    val location = IntArray(2)
                    targetSquare.getLocationOnScreen(location)
                    val squareX = location[0]
                    val squareY = location[1]

                    val maxW = (screenSize.x - squareX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - squareY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (currentFrameWidthPx + dx).coerceIn(minSizePx, maxW)
                    val newH = (currentFrameHeightPx + dy).coerceIn(minSizePx, maxH)

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
}
'''

# FILE 3: floating_search_area_frame.xml (Outer Resize Handle & 4 Side Drag Handles)
FILES_TO_PATCH["app/src/main/res/layout/floating_search_area_frame.xml"] = '''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/rootSearchArea"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:clipChildren="false"
    android:clipToPadding="false">

    <!-- 1. ПЛАВАЮЩИЙ ТУЛБАР ЗОНЫ ПОИСКА -->
    <LinearLayout
        android:id="@+id/layoutSearchTopBar"
        android:layout_width="wrap_content"
        android:layout_height="40dp"
        android:layout_gravity="top|center_horizontal"
        android:layout_marginTop="20dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="8dp"
        android:paddingEnd="8dp"
        android:elevation="24dp">

        <TextView
            android:id="@+id/handleMoveSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="⁝⁝ ЗОНА"
            android:textColor="@color/electric_cyan"
            android:textSize="11sp"
            android:textStyle="bold"
            android:paddingStart="4dp"
            android:paddingEnd="8dp"
            android:layout_marginEnd="6dp" />

        <Button
            android:id="@+id/btnSaveSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="34dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:text="Сохранить зону"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/accent_blue"
            android:textSize="11sp"
            android:textStyle="bold"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:layout_marginEnd="6dp" />

        <Button
            android:id="@+id/btnResetSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="34dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:text="Сброс"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/bg_dark_blue"
            android:textSize="11sp"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:layout_marginEnd="6dp" />

        <ImageButton
            android:id="@+id/btnCancelSearchArea"
            android:layout_width="34dp"
            android:layout_height="34dp"
            android:src="@drawable/ic_close"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="6dp"
            android:contentDescription="Close" />
    </LinearLayout>

    <!-- 2. РАМКА ЗОНЫ ПОИСКА С 4 МАНИПУЛЯТОРАМИ -->
    <RelativeLayout
        android:id="@+id/layoutSearchFrameWithHandles"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_gravity="center"
        android:clipChildren="false"
        android:clipToPadding="false"
        android:elevation="16dp">

        <FrameLayout
            android:id="@+id/viewSearchAreaFrame"
            android:layout_width="220dp"
            android:layout_height="220dp"
            android:layout_marginTop="16dp"
            android:layout_marginBottom="16dp"
            android:layout_marginStart="16dp"
            android:layout_marginEnd="16dp"
            android:background="@drawable/border_yellow_search_area">

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_gravity="center"
                android:background="#E60D1117"
                android:paddingStart="8dp"
                android:paddingEnd="8dp"
                android:paddingTop="4dp"
                android:paddingBottom="4dp"
                android:text="Область поиска ИИ"
                android:textColor="@color/gold_accent"
                android:textSize="12sp"
                android:textStyle="bold" />
        </FrameLayout>

        <!-- МАНИПУЛЯТОРЫ ПО 4 СТОРОНАМ -->
        <TextView
            android:id="@+id/handleMoveSearchTop"
            android:layout_width="36dp"
            android:layout_height="18dp"
            android:layout_alignTop="@id/viewSearchAreaFrame"
            android:layout_centerHorizontal="true"
            android:layout_marginTop="-9dp"
            android:gravity="center"
            android:text="•••"
            android:textColor="@color/electric_cyan"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <TextView
            android:id="@+id/handleMoveSearchBottom"
            android:layout_width="36dp"
            android:layout_height="18dp"
            android:layout_alignBottom="@id/viewSearchAreaFrame"
            android:layout_centerHorizontal="true"
            android:layout_marginBottom="-9dp"
            android:gravity="center"
            android:text="•••"
            android:textColor="@color/electric_cyan"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <TextView
            android:id="@+id/handleMoveSearchLeft"
            android:layout_width="18dp"
            android:layout_height="36dp"
            android:layout_alignLeft="@id/viewSearchAreaFrame"
            android:layout_centerVertical="true"
            android:layout_marginLeft="-9dp"
            android:gravity="center"
            android:text=":\n:"
            android:textColor="@color/electric_cyan"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <TextView
            android:id="@+id/handleMoveSearchRight"
            android:layout_width="18dp"
            android:layout_height="36dp"
            android:layout_alignRight="@id/viewSearchAreaFrame"
            android:layout_centerVertical="true"
            android:layout_marginRight="-9dp"
            android:gravity="center"
            android:text=":\n:"
            android:textColor="@color/electric_cyan"
            android:textSize="10sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:elevation="20dp" />

        <!-- ВЫНЕСЕННЫЙ РЕСАЙЗ СНИЗУ-СПРАВА -->
        <ImageView
            android:id="@+id/handleResizeSearchArea"
            android:layout_width="36dp"
            android:layout_height="36dp"
            android:layout_below="@id/viewSearchAreaFrame"
            android:layout_toEndOf="@id/viewSearchAreaFrame"
            android:layout_marginTop="-12dp"
            android:layout_marginStart="-12dp"
            android:src="@drawable/handle_manipulator_bg"
            android:padding="4dp"
            android:elevation="22dp"
            android:contentDescription="Resize Search Area" />
    </RelativeLayout>
</FrameLayout>
'''

# FILE 4: SearchAreaOverlay.kt (Binding 4 Side Manipulators)
FILES_TO_PATCH["app/src/main/java/com/example/autotap/ui/overlays/SearchAreaOverlay.kt"] = '''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Rect
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.CoordConverter
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class SearchAreaOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val minSizePx = 30.dpToPx(context)
    private var currentWidthPx = 200.dpToPx(context)
    private var currentHeightPx = 200.dpToPx(context)

    private var viewSearchAreaFrameView: View? = null
    private var topBarView: View? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.floating_search_area_frame, null)

        viewSearchAreaFrameView = view.findViewByNames("viewSearchAreaFrame")
        topBarView = view.findViewByNames("layoutSearchTopBar")

        view.bindClickByNames("btnSaveSearchArea") {
            val svc = MyAutoClickService.instance
            val frame = viewSearchAreaFrameView
            if (svc != null && frame != null) {
                val screenSize = context.getRealScreenSize()
                val location = IntArray(2)
                frame.getLocationOnScreen(location)

                val exactX = location[0]
                val exactY = location[1]
                val exactW = frame.width.takeIf { it > 0 } ?: currentWidthPx
                val exactH = frame.height.takeIf { it > 0 } ?: currentHeightPx

                val rectPx = Rect(exactX, exactY, exactX + exactW, exactY + exactH)
                val rectNorm = CoordConverter.toNormalizedRect(rectPx, screenSize.x, screenSize.y)

                if (svc.actionsList.isNotEmpty()) {
                    val currentAction = svc.actionsList.last()
                    currentAction.customSearchArea = true
                    currentAction.searchAreaX = exactX
                    currentAction.searchAreaY = exactY
                    currentAction.searchAreaW = exactW
                    currentAction.searchAreaH = exactH
                    StructuredLogger.logDiagnostic("AI_SCANNER", "Зона поиска сохранена: (" + exactX + ", " + exactY + ", " + exactW + "x" + exactH + "px), norm=" + rectNorm)
                }
            }
            context.vibrateFeedback()
            hide()
        }

        view.bindClickByNames("btnResetSearchArea") {
            currentWidthPx = 200.dpToPx(context)
            currentHeightPx = 200.dpToPx(context)
            val frame = viewSearchAreaFrameView
            if (frame != null) {
                val lp = frame.layoutParams
                if (lp != null) {
                    lp.width = currentWidthPx
                    lp.height = currentHeightPx
                    frame.layoutParams = lp
                    frame.requestLayout()
                }
            }
            context.vibrateFeedback()
            StructuredLogger.logDiagnostic("AI_SCANNER", "Размер области поиска сброшен.")
        }

        view.bindClickByNames("btnCancelSearchArea", "btnCloseSearchArea") {
            hide()
        }

        val topBar = topBarView
        if (topBar != null) {
            setupIndependentViewDrag(topBar)
        }

        val frameContainer = view.findViewByNames("layoutSearchFrameWithHandles") ?: viewSearchAreaFrameView
        val frameView = viewSearchAreaFrameView

        if (frameContainer != null) {
            setupIndependentViewDrag(frameContainer)
        }

        val hTop = view.findViewByNames("handleMoveSearchTop")
        val hBottom = view.findViewByNames("handleMoveSearchBottom")
        val hLeft = view.findViewByNames("handleMoveSearchLeft")
        val hRight = view.findViewByNames("handleMoveSearchRight")

        if (frameContainer != null) {
            hTop?.let { setupIndependentViewDrag(it, frameContainer) }
            hBottom?.let { setupIndependentViewDrag(it, frameContainer) }
            hLeft?.let { setupIndependentViewDrag(it, frameContainer) }
            hRight?.let { setupIndependentViewDrag(it, frameContainer) }
        }

        val resizeHandle = view.findViewByNames("handleResizeSearchArea")
        if (resizeHandle != null && frameView != null) {
            setupCornerResizeHandler(resizeHandle, frameView)
        }

        return view
    }

    private fun setupIndependentViewDrag(touchView: View, targetViewToDrag: View = touchView) {
        var startTouchX = 0f
        var startTouchY = 0f
        var initialTranslationX = 0f
        var initialTranslationY = 0f

        touchView.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startTouchX = event.rawX
                    startTouchY = event.rawY
                    initialTranslationX = targetViewToDrag.translationX
                    initialTranslationY = targetViewToDrag.translationY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - startTouchX
                    val dy = event.rawY - startTouchY

                    targetViewToDrag.translationX = initialTranslationX + dx
                    targetViewToDrag.translationY = initialTranslationY + dy
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    true
                }
                else -> false
            }
        }
    }

    private fun setupCornerResizeHandler(resizeView: View, targetFrame: View) {
        var lastTouchX = 0f
        var lastTouchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    lastTouchX = event.rawX
                    lastTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - lastTouchX).toInt()
                    val dy = (event.rawY - lastTouchY).toInt()

                    lastTouchX = event.rawX
                    lastTouchY = event.rawY

                    val location = IntArray(2)
                    targetFrame.getLocationOnScreen(location)
                    val windowX = location[0]
                    val windowY = location[1]

                    val maxW = (screenSize.x - windowX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - windowY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (currentWidthPx + dx).coerceIn(minSizePx, maxW)
                    val newH = (currentHeightPx + dy).coerceIn(minSizePx, maxH)

                    currentWidthPx = newW
                    currentHeightPx = newH

                    val lp = targetFrame.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetFrame.layoutParams = lp
                        targetFrame.requestLayout()
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
}
'''

# -----------------------------------------------------------------------------
# 3. APPLYING PATCHES WITH TRUNCATE GUARD
# -----------------------------------------------------------------------------

def apply_patch():
    print("[🚀] Starting AutoTap Outer Resize & 4 Side Handles Patch (v58)...")
    patched_count = 0
    
    for rel_path, new_content in FILES_TO_PATCH.items():
        abs_path = os.path.abspath(rel_path)
        dir_path = os.path.dirname(abs_path)
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        print(f"[*] Patching file: {rel_path}...")
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.truncate(0)
            f.write(new_content)
        
        patched_count += 1

    print(f"\n[🎉] SUCCESS: Successfully applied v58 External Resize & 4 Handles Patch to {patched_count} files!")
    print("[✓] Resize handle is 100% OUTSIDE the crop box (zero overlap inside).")
    print("[✓] Added 4 middle-side move handles (top, bottom, left, right).")

if __name__ == '__main__':
    apply_patch()