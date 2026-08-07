#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re

class PrecisionPatcher:
    """
    Движок патчинга v40 Precision Architecture.
    """
    def __init__(self, file_path, content=None):
        self.file_path = os.path.abspath(file_path)
        if content is not None:
            self.content = content
        else:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"Файл не найден: {self.file_path}")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()

    def validate_brackets(self):
        clean = re.sub(r'/\*[\s\S]*?\*/', '', self.content)
        clean = re.sub(r'//.*', '', clean)
        clean = re.sub(r'"""[\s\S]*?"""', '""', clean)
        clean = re.sub(r'"([^"\\]|\\.)*"', '""', clean)
        clean = re.sub(r"'([^'\\]|\\.)*'", "''", clean)

        brackets = {'(': ')', '{': '}', '[': ']'}
        stack = []
        for char in clean:
            if char in brackets.keys():
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    raise ValueError(f"Ошибка скобок в {self.file_path}: Лишняя закрывающая скобка '{char}'")
                top = stack.pop()
                if brackets[top] != char:
                    raise ValueError(f"Ошибка скобок в {self.file_path}: Несоответствие скобок '{top}' и '{char}'")
        if stack:
            raise ValueError(f"Ошибка скобок в {self.file_path}: Незакрытые скобки {stack}")

    def apply(self):
        if self.file_path.endswith(".kt"):
            self.validate_brackets()
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
        print(f"🟢 SUCCESS: {os.path.basename(self.file_path)}")


# ==============================================================================
# 1. OVERLAY BASE (ПОЛНОЭКРАННЫЕ ГРАНИЦЫ И БЕЗЛИМИТНОЕ ПЕРЕМЕЩЕНИЕ)
# ==============================================================================
OVERLAY_BASE_CONTENT = """package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Rect
import android.os.Build
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import androidx.core.view.ViewCompat
import com.example.autotap.createOverlayParams
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.safeAddView
import com.example.autotap.safeRemoveView
import kotlin.math.abs

abstract class OverlayBase(
    protected val context: Context,
    val overlayManager: OverlayManager,
    var layer: OverlayLayer = OverlayLayer.PANEL_LAYER,
    var priority: OverlayPriority = OverlayPriority.MEDIUM
) {
    protected val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    open val layoutResId: Int = 0

    var width: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var height: Int = WindowManager.LayoutParams.WRAP_CONTENT
    var gravity: Int = Gravity.TOP or Gravity.START
    var flags: Int = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
    var dimAmount: Float = 0.5f

    var initialX: Int = 100
    var initialY: Int = 200

    protected var overlayView: View? = null
    protected var rootView: View? = null
    protected var layoutParams: WindowManager.LayoutParams? = null
    protected var params: WindowManager.LayoutParams? = null
    var isShowing: Boolean = false
        protected set

    private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop

    open fun createView(): View {
        if (layoutResId != 0) {
            return LayoutInflater.from(context).inflate(layoutResId, null)
        }
        throw UnsupportedOperationException("Оверлей должен переопределить layoutResId или createView()")
    }

    open fun inflate() {
        if (rootView != null) return
        val view = createView()
        rootView = view
        overlayView = view

        val targetX = if (width == WindowManager.LayoutParams.MATCH_PARENT) 0 else initialX
        val targetY = if (height == WindowManager.LayoutParams.MATCH_PARENT) 0 else initialY

        val lp = createOverlayParams(
            width = width,
            height = height,
            gravity = gravity,
            flags = flags,
            x = targetX,
            y = targetY
        ).apply {
            if (this@OverlayBase.dimAmount > 0f && (flags and WindowManager.LayoutParams.FLAG_DIM_BEHIND) != 0) {
                this.dimAmount = this@OverlayBase.dimAmount
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                this.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        this.layoutParams = lp
        this.params = lp
        ViewCompat.setImportantForAccessibility(
            view,
            ViewCompat.IMPORTANT_FOR_ACCESSIBILITY_NO
        )
    }

    open fun show() {
        val currentView = overlayView
        if (isShowing && currentView != null) {
            try {
                windowManager.safeRemoveView(currentView)
            } catch (_: Exception) {}
            isShowing = false
        }

        try {
            inflate()
            val view = overlayView ?: rootView ?: return
            val lp = layoutParams ?: params ?: return
            reboundToScreen(lp)
            val added = windowManager.safeAddView(view, lp)
            if (added) {
                isShowing = true
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} (слой=${layer.name}) принудительно отображен.")
            }
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка при отображении ${javaClass.simpleName}", e)
        }
    }

    open fun hide() {
        val view = overlayView ?: rootView ?: return
        if (isShowing) {
            try {
                windowManager.safeRemoveView(view)
                logDiagnostic("OVERLAY", "Оверлей ${javaClass.simpleName} скрыт.")
            } catch (e: Exception) {
                logError("OVERLAY", "Ошибка при скрытии ${javaClass.simpleName}", e)
            }
            overlayView = null
            rootView = null
            isShowing = false
        }
    }

    fun reboundToScreen(lp: WindowManager.LayoutParams) {
        if (width == WindowManager.LayoutParams.MATCH_PARENT && height == WindowManager.LayoutParams.MATCH_PARENT) {
            lp.x = 0
            lp.y = 0
            return
        }
        val screenSize = context.getRealScreenSize()
        val maxX = screenSize.x.coerceAtLeast(10)
        val maxY = screenSize.y.coerceAtLeast(10)
        lp.x = lp.x.coerceIn(-100, maxX)
        lp.y = lp.y.coerceIn(-100, maxY)
    }

    open fun updatePosition(x: Int, y: Int) {
        val lp = layoutParams ?: params ?: return
        if (width != WindowManager.LayoutParams.MATCH_PARENT) {
            val screenSize = context.getRealScreenSize()
            val viewW = overlayView?.width ?: 200
            val viewH = overlayView?.height ?: 200
            val maxX = (screenSize.x - viewW + 100).coerceAtLeast(0)
            val maxY = (screenSize.y - viewH + 100).coerceAtLeast(0)
            lp.x = x.coerceIn(-100, maxX)
            lp.y = y.coerceIn(-100, maxY)
        } else {
            lp.x = 0
            lp.y = 0
        }
        val v = overlayView ?: rootView ?: return
        try {
            windowManager.updateViewLayout(v, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления позиции $layer", e)
        }
    }

    fun setTouchable(touchable: Boolean) {
        val lp = layoutParams ?: params ?: return
        val view = overlayView ?: rootView ?: return
        if (touchable) {
            lp.flags = lp.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
        } else {
            lp.flags = lp.flags or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
        }
        try {
            windowManager.updateViewLayout(view, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления флага touchable", e)
        }
    }

    fun getBounds(): Rect {
        val lp = layoutParams ?: params ?: return Rect(0, 0, 0, 0)
        val w = if (width > 0) width else 200
        val h = if (height > 0) height else 200
        return Rect(lp.x, lp.y, lp.x + w, lp.y + h)
    }

    protected fun setupDragAndDrop(handleView: View) {
        var startX = 0
        var startY = 0
        var touchX = 0f
        var touchY = 0f
        var isDragging = false

        handleView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = lp.x
                    startY = lp.y
                    touchX = event.rawX
                    touchY = event.rawY
                    isDragging = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    if (!isDragging && (abs(dx) > touchSlop || abs(dy) > touchSlop)) {
                        isDragging = true
                    }

                    if (isDragging) {
                        val newX = startX + dx
                        val newY = startY + dy
                        updatePosition(newX, newY)
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    val wasDragging = isDragging
                    isDragging = false
                    if (!wasDragging) {
                        handleView.performClick()
                    }
                    true
                }
                else -> false
            }
        }
    }
}
"""


# ==============================================================================
# 2. CAPTURE FRAME OVERLAY (УМНОЕ ПОЗИЦИОНИРОВАНИЕ И 100% КРАЕВОЙ КРОП)
# ==============================================================================
CAPTURE_FRAME_OVERLAY_CONTENT = """package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.graphics.PointF
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.LinearLayout
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback
import kotlin.math.max

class CaptureFrameOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CAPTURE_LAYER, OverlayPriority.HIGH) {

    override val layoutResId: Int = R.layout.floating_capture_frame

    private val minSizePx = 24.dpToPx(context)
    private var currentFrameWidthPx = 140.dpToPx(context)
    private var currentFrameHeightPx = 140.dpToPx(context)

    private var layoutCaptureContainer: LinearLayout? = null
    private var layoutTopBar: View? = null
    private var layoutBottomBar: View? = null
    private var captureSquare: FrameLayout? = null

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

        layoutCaptureContainer = view.findViewByNames("layoutCaptureContainer") as? LinearLayout
        layoutTopBar = view.findViewByNames("layoutTopBar")
        layoutBottomBar = view.findViewByNames("layoutBottomBar")
        captureSquare = view.findViewByNames("captureSquare") as? FrameLayout

        view.bindClickByNames("btnDoCapture", "btn_do_capture", "btn_capture") {
            logDiagnostic("OVERLAY", "Вырезание маски с экрана (${currentFrameWidthPx}x${currentFrameHeightPx}px)")
            context.vibrateFeedback()

            val svc = MyAutoClickService.instance
            val lp = layoutParams ?: params
            val square = captureSquare
            if (svc != null && lp != null && square != null) {
                val fullBitmap = svc.captureScreenBitmap()
                if (fullBitmap != null && fullBitmap.width > 20 && fullBitmap.height > 20) {
                    // АБСОЛЮТНЫЙ РАСЧЕТ КООРДИНАТ КВАДРАТА ПРИЦЕЛА НА ЭКРАНЕ
                    val squareLeftOnScreen = lp.x + square.left
                    val squareTopOnScreen = lp.y + square.top

                    val safeX = squareLeftOnScreen.coerceIn(0, (fullBitmap.width - 20).coerceAtLeast(0))
                    val safeY = squareTopOnScreen.coerceIn(0, (fullBitmap.height - 20).coerceAtLeast(0))
                    val safeW = currentFrameWidthPx.coerceIn(10, fullBitmap.width - safeX)
                    val safeH = currentFrameHeightPx.coerceIn(10, fullBitmap.height - safeY)

                    val metrics = context.resources.displayMetrics
                    val centerXNorm = (safeX + safeW / 2f) / metrics.widthPixels.toFloat()
                    val centerYNorm = (safeY + safeH / 2f) / metrics.heightPixels.toFloat()

                    val nextTemplateIndex = svc.templateRepository.getNextFreeTemplateIndex()

                    val action = ActionConfig(
                        type = ActionType.AI_SEARCH,
                        xNorm = centerXNorm.coerceIn(0f, 1f),
                        yNorm = centerYNorm.coerceIn(0f, 1f),
                        selectedTemplateIndex = nextTemplateIndex
                    )
                    svc.actionsList.add(action)

                    if (safeW > 10 && safeH > 10) {
                        val croppedMask = Bitmap.createBitmap(fullBitmap, safeX, safeY, safeW, safeH)
                        svc.templateRepository.saveTemplate(nextTemplateIndex, croppedMask)
                        logDiagnostic("AI_SCANNER", "Безопасный точный кроп: шаблон #$nextTemplateIndex сохранен (${safeW}x${safeH}px).")

                        val calibrated = svc.templateRepository.loadCalibratedMask(nextTemplateIndex)
                        if (calibrated != null) {
                            overlayManager.debuggerOverlay.show()
                            overlayManager.debuggerOverlay.showCandidates(listOf(
                                com.example.autotap.engine.ai.MatchCandidate(
                                    point = PointF(safeX + safeW / 2f, safeY + safeH / 2f),
                                    score = 1.0f,
                                    boundingBox = calibrated.boundingBox,
                                    scale = 1.0f,
                                    templateIndex = nextTemplateIndex
                                )
                            ))
                        }
                    }
                }
            }
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCancelCapture", "btn_cancel_capture", "btn_close") {
            hide()
            overlayManager.showControlPanel()
        }

        view.bindClickByNames("btnCaptureSearchArea") {
            logDiagnostic("OVERLAY", "Переход к настройке области поиска.")
            overlayManager.searchAreaOverlay.show()
            hide()
        }

        val moveHandle = view.findViewByNames("handleMoveFrame") ?: view
        setupDragAndDrop(moveHandle)

        val sq = captureSquare
        val resizeHandle = view.findViewByNames("handleResize")
        if (resizeHandle != null && sq != null) {
            setupResizeHandler(resizeHandle, sq)
        }

        return view
    }

    override fun updatePosition(x: Int, y: Int) {
        val lp = layoutParams ?: params ?: return
        val screenSize = context.getRealScreenSize()
        val squareW = currentFrameWidthPx
        val squareH = currentFrameHeightPx

        // Разрешаем прицелу подходить вплотную к 0-границе экрана
        val topOffset = layoutTopBar?.height ?: 120
        val minX = -50
        val minY = -topOffset
        val maxX = screenSize.x - 50
        val maxY = screenSize.y - 50

        lp.x = x.coerceIn(minX, maxX)
        lp.y = y.coerceIn(minY, maxY)

        // УМНОЕ АВТО-ПОЗИЦИОНИРОВАНИЕ ПАНЕЛЕЙ КНОПОК ПРИ ПРИБЛИЖЕНИИ К КРАЯМ
        applySmartPanelFlipping(lp.y, screenSize.y)

        val v = overlayView ?: rootView ?: return
        try {
            windowManager.updateViewLayout(v, lp)
        } catch (e: Exception) {
            logError("OVERLAY", "Ошибка обновления позиции прицела", e)
        }
    }

    private fun applySmartPanelFlipping(currentY: Int, screenHeight: Int) {
        val container = layoutCaptureContainer ?: return
        val topBar = layoutTopBar ?: return
        val bottomBar = layoutBottomBar ?: return
        val square = captureSquare ?: return

        container.removeAllViews()

        if (currentY < 120) {
            // ВЕРХНИЙ КРАЙ: Верхняя панель переворачивается И ПОДСТАВЛЯЕТСЯ ПОД ПРИЦЕЛ
            container.addView(square)
            container.addView(topBar)
            container.addView(bottomBar)
        } else if (currentY > screenHeight - (currentFrameHeightPx + 200)) {
            // НИЖНИЙ КРАЙ: Нижняя панель поднимается НАД ПРИЦЕЛОМ
            container.addView(topBar)
            container.addView(bottomBar)
            container.addView(square)
        } else {
            // О Б Ы Ч Н Ы Й   Р Е Ж И М
            container.addView(topBar)
            container.addView(square)
            container.addView(bottomBar)
        }
    }

    private fun setupResizeHandler(resizeView: View, captureSquare: FrameLayout) {
        var startW = 0
        var startH = 0
        var touchX = 0f
        var touchY = 0f

        resizeView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startW = captureSquare.width.takeIf { it > 0 } ?: currentFrameWidthPx
                    startH = captureSquare.height.takeIf { it > 0 } ?: currentFrameHeightPx
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchX).toInt()
                    val dy = (event.rawY - touchY).toInt()

                    currentFrameWidthPx = max(minSizePx, startW + dx)
                    currentFrameHeightPx = max(minSizePx, startH + dy)

                    val sqLp = captureSquare.layoutParams
                    if (sqLp != null) {
                        sqLp.width = currentFrameWidthPx
                        sqLp.height = currentFrameHeightPx
                        captureSquare.layoutParams = sqLp
                    }

                    try {
                        windowManager.updateViewLayout(overlayView ?: rootView, lp)
                    } catch (e: Exception) {
                        logError("OVERLAY", "Ошибка ресайза прицела", e)
                    }
                    true
                }
                else -> false
            }
        }
    }
}
"""


def main():
    base_dir = os.getcwd()
    print("=== ЗАПУСК ПАТЧИНГА V40 (Умное позиционирование и 100% краевой прицел) ===")

    files_map = {
        "app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt": OVERLAY_BASE_CONTENT,
        "app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt": CAPTURE_FRAME_OVERLAY_CONTENT,
    }

    try:
        for rel_path, content in files_map.items():
            full_path = os.path.join(base_dir, rel_path)
            patcher = PrecisionPatcher(full_path, content)
            patcher.apply()

        print("🟢 ВСЕ КРАЕВОЙ И УМНЫЙ ФУНКЦИОНАЛ ПРИЦЕЛА УСПЕШНО ПРИМЕНЕН!")
    except Exception as e:
        print(f"❌ ОШИБКА ПАТЧИНГА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()