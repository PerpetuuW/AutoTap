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
# 2. DEFINITIONS OF UPDATED FILES (V46 DYNAMIC TOOLBAR DOCKING)
# -----------------------------------------------------------------------------

FILES_TO_PATCH = {}

# FILE 1: CaptureFrameOverlay.kt (Dynamic Edge-Aware Toolbar Docking)
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
            logDiagnostic("CAPTURE_FRAME", "Снятие шаблона (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
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

                val screenSize = context.getRealScreenSize()
                val cropNormX = ((cropX + cropW / 2f) / screenSize.x.toFloat()).coerceIn(0f, 1f)
                val cropNormY = ((cropY + cropH / 2f) / screenSize.y.toFloat()).coerceIn(0f, 1f)

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
                                        safeW,
                                        safeH
                                    )
                                } catch (e: Exception) {
                                    logError("CAPTURE_FRAME", "Ошибка создания Bitmap кропа маски", e)
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

        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        val topBar = topBarView ?: view

        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)

        val sq = captureSquareView
        if (sq != null) {
            setupDragAndDrop(sq)
        }

        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && sq != null) {
            setupCornerResizeHandler(resizeHandle, sq)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        updateDynamicToolbarDocking(x, y)
    }

    // 💥 ДИНАМИЧЕСКИЙ РАСЧЕТ ПРИЛИПАНИЯ ТУЛБАРА К КРАЯМ ЭКРАНА
    private fun updateDynamicToolbarDocking(currentX: Int, currentY: Int) {
        val square = captureSquareView ?: return
        val topBar = topBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 180.dpToPx(context)
        val squareWidth = square.width.takeIf { it > 0 } ?: currentFrameWidthPx
        val squareHeight = square.height.takeIf { it > 0 } ?: currentFrameHeightPx
        val gap = 6.dpToPx(context)

        // 1. ВЕРТИКАЛЬНАЯ ПРОВЕРКА (Если уперлись в самый ВЕРХ -> Тулбар прыгает ПОД рамку)
        if (currentY < (topBarHeight + gap)) {
            topBar.translationY = (squareHeight + gap * 2).toFloat()
        } else {
            topBar.translationY = 0f
        }

        // 2. ГОРИЗОНТАЛЬНАЯ ПРОВЕРКА (Смещение к центру, чтобы кнопки не уходили за экран)
        val idealX = currentX + (squareWidth - topBarWidth) / 2
        val clampedX = idealX.coerceIn(0, (screenSize.x - topBarWidth).coerceAtLeast(0))
        topBar.translationX = (clampedX - currentX).toFloat()
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
                    val currentLp = layoutParams ?: params
                    if (currentLp != null) {
                        updateDynamicToolbarDocking(currentLp.x, currentLp.y)
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

# FILE 2: SearchAreaOverlay.kt (Dynamic Docking for Search Area)
FILES_TO_PATCH["app/src/main/java/com/example/autotap/ui/overlays/SearchAreaOverlay.kt"] = '''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Rect
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.LinearLayout
import com.example.autotap.CoordConverter
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class SearchAreaOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private val minSizePx = 30.dpToPx(context)
    private var currentWidthPx = 200.dpToPx(context)
    private var currentHeightPx = 200.dpToPx(context)

    private var viewSearchAreaFrameView: View? = null
    private var topBarView: View? = null

    init {
        gravity = Gravity.TOP or Gravity.START
        layer = OverlayLayer.CAPTURE_LAYER
        priority = OverlayPriority.HIGH
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
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
                    logDiagnostic("AI_SCANNER", "Зона поиска сохранена: (" + exactX + ", " + exactY + ", " + exactW + "x" + exactH + "px), norm=" + rectNorm)
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
            logDiagnostic("AI_SCANNER", "Размер области поиска сброшен.")
        }

        view.bindClickByNames("btnCancelSearchArea", "btnCloseSearchArea") {
            hide()
        }

        val moveHandle = view.findViewByNames("handleMoveSearchArea") ?: view
        val topBar = topBarView ?: view
        setupDragAndDrop(moveHandle)
        setupDragAndDrop(topBar)

        val frameView = viewSearchAreaFrameView
        if (frameView != null) {
            setupDragAndDrop(frameView)
        }

        val resizeHandle = view.findViewByNames("handleResizeSearchArea")
        if (resizeHandle != null && frameView != null) {
            setupCornerResizeHandler(resizeHandle, frameView)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        super.updatePosition(x, y)
        updateDynamicToolbarDocking(x, y)
    }

    private fun updateDynamicToolbarDocking(currentX: Int, currentY: Int) {
        val frame = viewSearchAreaFrameView ?: return
        val topBar = topBarView ?: return
        val screenSize = context.getRealScreenSize()

        val topBarHeight = topBar.height.takeIf { it > 0 } ?: 38.dpToPx(context)
        val topBarWidth = topBar.width.takeIf { it > 0 } ?: 180.dpToPx(context)
        val squareWidth = frame.width.takeIf { it > 0 } ?: currentWidthPx
        val squareHeight = frame.height.takeIf { it > 0 } ?: currentHeightPx
        val gap = 6.dpToPx(context)

        if (currentY < (topBarHeight + gap)) {
            topBar.translationY = (squareHeight + gap * 2).toFloat()
        } else {
            topBar.translationY = 0f
        }

        val idealX = currentX + (squareWidth - topBarWidth) / 2
        val clampedX = idealX.coerceIn(0, (screenSize.x - topBarWidth).coerceAtLeast(0))
        topBar.translationX = (clampedX - currentX).toFloat()
    }

    private fun setupCornerResizeHandler(resizeView: View, targetFrame: View) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val screenSize = context.getRealScreenSize()

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = targetFrame.width.takeIf { it > 0 } ?: currentWidthPx
                    startH = targetFrame.height.takeIf { it > 0 } ?: currentHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    val location = IntArray(2)
                    targetFrame.getLocationOnScreen(location)
                    val windowX = location[0]
                    val windowY = location[1]

                    val maxW = (screenSize.x - windowX - 4.dpToPx(context)).coerceAtLeast(minSizePx)
                    val maxH = (screenSize.y - windowY - 40.dpToPx(context)).coerceAtLeast(minSizePx)

                    val newW = (startW + dx).coerceIn(minSizePx, maxW)
                    val newH = (startH + dy).coerceIn(minSizePx, maxH)

                    currentWidthPx = newW
                    currentHeightPx = newH

                    val lp = targetFrame.layoutParams
                    if (lp != null) {
                        lp.width = newW
                        lp.height = newH
                        targetFrame.layoutParams = lp
                        targetFrame.requestLayout()
                    }
                    val currentLp = layoutParams ?: params
                    if (currentLp != null) {
                        updateDynamicToolbarDocking(currentLp.x, currentLp.y)
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

# FILE 3: floating_capture_frame.xml (Unclipped Container Layout)
FILES_TO_PATCH["app/src/main/res/layout/floating_capture_frame.xml"] = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/layoutCaptureContainer"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:gravity="center_horizontal"
    android:padding="0dp"
    android:clipChildren="false"
    android:clipToPadding="false"
    android:elevation="18dp">

    <!-- ТУЛБАР КНОПОК ПРИЦЕЛА -->
    <LinearLayout
        android:id="@+id/layoutTopBar"
        android:layout_width="wrap_content"
        android:layout_height="38dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="6dp"
        android:paddingEnd="6dp"
        android:layout_marginBottom="4dp">

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

    <!-- ПОЛЕ ШАБЛОНА + ВЫНЕСЕННЫЙ РЕГУЛЯТОР РЕСАЙЗА -->
    <RelativeLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:clipChildren="false"
        android:clipToPadding="false"
        android:paddingEnd="16dp"
        android:paddingBottom="16dp">

        <FrameLayout
            android:id="@+id/captureSquare"
            android:layout_width="160dp"
            android:layout_height="160dp"
            android:background="@drawable/border_capture_square" />

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
            android:contentDescription="Resize Grip" />
    </RelativeLayout>
</LinearLayout>
'''

# FILE 4: floating_search_area_frame.xml (Unclipped Search Container)
FILES_TO_PATCH["app/src/main/res/layout/floating_search_area_frame.xml"] = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/rootSearchArea"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:gravity="center_horizontal"
    android:padding="0dp"
    android:clipChildren="false"
    android:clipToPadding="false"
    android:elevation="18dp">

    <!-- ВЕРХНИЙ ТУЛБАР -->
    <LinearLayout
        android:id="@+id/layoutSearchTopBar"
        android:layout_width="wrap_content"
        android:layout_height="38dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="6dp"
        android:paddingEnd="6dp"
        android:layout_marginBottom="4dp">

        <Button
            android:id="@+id/btnSaveSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="32dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:text="Задать зону"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/accent_blue"
            android:textSize="11sp"
            android:textStyle="bold"
            android:paddingStart="8dp"
            android:paddingEnd="8dp"
            android:layout_marginEnd="4dp" />

        <Button
            android:id="@+id/btnResetSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="32dp"
            android:minWidth="0dp"
            android:minHeight="0dp"
            android:text="Сброс"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/bg_dark_blue"
            android:textSize="11sp"
            android:paddingStart="8dp"
            android:paddingEnd="8dp"
            android:layout_marginEnd="4dp" />

        <ImageButton
            android:id="@+id/btnCancelSearchArea"
            android:layout_width="32dp"
            android:layout_height="32dp"
            android:src="@drawable/ic_close"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="5dp"
            android:contentDescription="Close" />
    </LinearLayout>

    <!-- ЗОНА ПОИСКА + ВЫНЕСЕННЫЙ РЕГУЛЯТОР РЕСАЙЗА -->
    <RelativeLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:clipChildren="false"
        android:clipToPadding="false"
        android:paddingEnd="16dp"
        android:paddingBottom="16dp">

        <FrameLayout
            android:id="@+id/viewSearchAreaFrame"
            android:layout_width="220dp"
            android:layout_height="220dp"
            android:layout_gravity="center_horizontal"
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
                android:text="Зона поиска ИИ"
                android:textColor="@color/gold_accent"
                android:textSize="12sp"
                android:textStyle="bold" />
        </FrameLayout>

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
            android:contentDescription="Resize Search Area" />
    </RelativeLayout>

    <!-- НИЖНИЙ ТУЛБАР ПЕРЕМЕЩЕНИЯ -->
    <LinearLayout
        android:id="@+id/layoutSearchBottomBar"
        android:layout_width="wrap_content"
        android:layout_height="28dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:background="@drawable/drag_handle_bg"
        android:paddingStart="8dp"
        android:paddingEnd="8dp"
        android:layout_marginTop="2dp">

        <TextView
            android:id="@+id/handleMoveSearchArea"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="ДВИГАТЬ ЗОНУ"
            android:textColor="@color/electric_cyan"
            android:textSize="10sp"
            android:textStyle="bold" />
    </LinearLayout>
</LinearLayout>
'''

# -----------------------------------------------------------------------------
# 3. APPLYING PATCHES WITH TRUNCATE GUARD
# -----------------------------------------------------------------------------

def apply_patch():
    print("[🚀] Starting AutoTap Dynamic Toolbar Docking Patch (v46)...")
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

    print(f"\n[🎉] SUCCESS: Successfully applied Dynamic Edge-Aware Docking Patch to {patched_count} files!")
    print("[✓] Topbar automatically jumps to BOTTOM when frame touches top edge.")
    print("[✓] Horizontal offset automatically clamped within screen bounds.")
    print("[✓] Collapse button icon unified to clean ≡ style.")

if __name__ == '__main__':
    apply_patch()