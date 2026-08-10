#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v61 - OUTSIDE RESIZE GRIP, AI TIMEOUT & INTERACTIVE BEACON CONFIRMATION
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
# 1. ActionConfig.kt (ДОБАВЛЕНИЕ ПОЛЯ AI TIMEOUT)
# =============================================================================
ACTION_CONFIG_KT = r'''package com.example.autotap.model

import android.graphics.PointF

enum class ActionType {
    CLICK, SWIPE, LONG_PRESS, AI_SEARCH, WAIT, LOAD_SCRIPT, JOYSTICK_PATH
}

data class ActionConfig(
    var type: ActionType = ActionType.CLICK,
    var xNorm: Float = 0.5f,
    var yNorm: Float = 0.5f,
    var endXNorm: Float = 0.5f,
    var endYNorm: Float = 0.5f,
    var randomRadius: Float = 0f,
    var delay: Long = 500L,
    var holdDuration: Long = 100L,
    var selectedTemplateIndex: Int = 0,
    var multiTemplateIndices: List<Int> = emptyList(),
    var similarityPercent: Int = 85,
    var scanIntervalSeconds: Float = 0.1f,
    var aiTimeoutSeconds: Float = 5.0f, // Таймаут поиска в секундах
    var clickAiTarget: Boolean = false,
    var loopUntilStopped: Boolean = true,
    var jumpToStepOnMatch: Int? = null,
    var jumpToStepOnFail: Int? = null,
    var targetScriptToLoad: String? = null,
    var customSearchArea: Boolean = false,
    var searchAreaX: Int = 0,
    var searchAreaY: Int = 0,
    var searchAreaW: Int = 0,
    var searchAreaH: Int = 0,
    var shapeOnlyMode: Boolean = false,
    var autoTuningMode: Boolean = true,
    var hybridCascadeMode: Boolean = true,
    var multiScaleSearch: Boolean = true,
    var joystickPath: List<PointF> = emptyList(),
    var swipePath: List<PointF> = emptyList(),
    var longPressDuration: Long = 500L,
    var clickOffsetX: Int = 0,
    var clickOffsetY: Int = 0,
    var notificationMode: Int = 0
)'''


# =============================================================================
# 2. floating_capture_frame.xml (РУЧКА РЕСАЙЗА ВЫНЕСЕНА ЗА ПРЕДЕЛЫ КАДРА)
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

    <!-- 1. ВЕРХНИЙ ТУЛБАР -->
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
            android:text="📐"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/accent_blue"
            android:textSize="12sp"
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

    <!-- 2. ПОЛНОСТЬЮ ЧИСТЫЙ ВНУТРЕННИЙ КАДР ПРИЦЕЛА -->
    <FrameLayout
        android:id="@+id/captureSquare"
        android:layout_width="160dp"
        android:layout_height="160dp"
        android:background="@drawable/border_capture_square" />

    <!-- 3. НИЖНИЙ ТУЛБАР С ВЫНЕСЕННОЙ РУЧКОЙ РЕСАЙЗА -->
    <LinearLayout
        android:id="@+id/layoutBottomBar"
        android:layout_width="wrap_content"
        android:layout_height="32dp"
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
            android:text="✥ ДВИГАТЬ"
            android:textColor="#FFB703"
            android:textSize="10sp"
            android:textStyle="bold"
            android:layout_marginEnd="8dp" />

        <!-- Ручка изменения размера вынесена за пределы кадра! -->
        <ImageView
            android:id="@+id/handleResize"
            android:layout_width="24dp"
            android:layout_height="24dp"
            android:src="@drawable/handle_manipulator_bg"
            android:padding="2dp"
            android:contentDescription="Resize Grip" />
    </LinearLayout>
</LinearLayout>'''


# =============================================================================
# 3. floating_edit_dialog.xml (ПОЛЕ НАСТРОЙКИ ТАЙМАУТА ПОИСКА)
# =============================================================================
EDIT_DIALOG_XML = r'''<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#CC000000"
    android:padding="16dp">

    <LinearLayout
        android:id="@+id/layoutEditCard"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:background="@drawable/panel_background"
        android:padding="16dp"
        android:elevation="22dp">

        <TextView
            android:id="@+id/tvEditTitle"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Настройка шага сценария"
            android:textColor="#00F5D4"
            android:textSize="18sp"
            android:textStyle="bold"
            android:layout_marginBottom="12dp" />

        <!-- 1. ПОДПИСЬ: Координаты X и Y -->
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Экранные координаты клика / ИИ-Якоря (X и Y px):"
            android:textColor="#58A6FF"
            android:textSize="12sp"
            android:textStyle="bold"
            android:layout_marginBottom="4dp"/>

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:layout_marginBottom="10dp">

            <LinearLayout
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:orientation="vertical">
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Координата X (px)"
                    android:textColor="@color/text_gray"
                    android:textSize="10sp"/>
                <EditText
                    android:id="@+id/etEditX"
                    android:layout_width="match_parent"
                    android:layout_height="42dp"
                    android:hint="X (px)"
                    android:inputType="number"
                    android:textColor="@color/text_white"
                    android:textColorHint="@color/text_gray"
                    android:background="@drawable/drag_handle_bg"
                    android:padding="8dp" />
            </LinearLayout>

            <View
                android:layout_width="8dp"
                android:layout_height="match_parent"/>

            <LinearLayout
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:orientation="vertical">
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Координата Y (px)"
                    android:textColor="@color/text_gray"
                    android:textSize="10sp"/>
                <EditText
                    android:id="@+id/etEditY"
                    android:layout_width="match_parent"
                    android:layout_height="42dp"
                    android:hint="Y (px)"
                    android:inputType="number"
                    android:textColor="@color/text_white"
                    android:textColorHint="@color/text_gray"
                    android:background="@drawable/drag_handle_bg"
                    android:padding="8dp" />
            </LinearLayout>
        </LinearLayout>

        <!-- 2. ПОДПИСЬ: Пауза / Задержка -->
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Пауза перед кликом (миллисекунды):"
            android:textColor="#58A6FF"
            android:textSize="12sp"
            android:textStyle="bold"
            android:layout_marginBottom="2dp"/>

        <EditText
            android:id="@+id/etEditDelayMs"
            android:layout_width="match_parent"
            android:layout_height="42dp"
            android:hint="Задержка (мс)"
            android:inputType="number"
            android:textColor="@color/text_white"
            android:textColorHint="@color/text_gray"
            android:background="@drawable/drag_handle_bg"
            android:padding="8dp"
            android:layout_marginBottom="12dp" />

        <!-- 3. ВЫБОР МАСОК И ТАЙМАУТ ПОИСКА -->
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Параметры ИИ-Мультипоиска и Таймаута:"
            android:textColor="#58A6FF"
            android:textSize="12sp"
            android:textStyle="bold"
            android:layout_marginBottom="4dp"/>

        <Button
            android:id="@+id/btnOpenTemplatePicker"
            android:layout_width="match_parent"
            android:layout_height="44dp"
            android:text="Открыть галерею масок с превью"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/accent_blue"
            android:textStyle="bold"
            android:textSize="12sp"
            android:layout_marginBottom="4dp"/>

        <TextView
            android:id="@+id/tvSelectedTemplatesSummary"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Выбранные маски: #0"
            android:textColor="#00F5D4"
            android:textSize="11sp"
            android:layout_marginBottom="10dp"/>

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:layout_marginBottom="10dp">

            <LinearLayout
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:orientation="vertical">
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Точность совпадения %"
                    android:textColor="@color/text_gray"
                    android:textSize="10sp"/>
                <EditText
                    android:id="@+id/etEditSimilarity"
                    android:layout_width="match_parent"
                    android:layout_height="40dp"
                    android:hint="85"
                    android:inputType="number"
                    android:textColor="@color/text_white"
                    android:background="@drawable/drag_handle_bg"
                    android:padding="8dp" />
            </LinearLayout>

            <View
                android:layout_width="8dp"
                android:layout_height="match_parent"/>

            <LinearLayout
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:orientation="vertical">
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Таймаут поиска (сек)"
                    android:textColor="@color/text_gray"
                    android:textSize="10sp"/>
                <EditText
                    android:id="@+id/etEditAiTimeout"
                    android:layout_width="match_parent"
                    android:layout_height="40dp"
                    android:hint="5.0"
                    android:inputType="numberDecimal"
                    android:textColor="@color/text_white"
                    android:background="@drawable/drag_handle_bg"
                    android:padding="8dp" />
            </LinearLayout>
        </LinearLayout>

        <CheckBox
            android:id="@+id/cbLoopUntilStopped"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Непрерывный мультипоиск до остановки"
            android:textColor="@color/text_white"
            android:textSize="12sp"
            android:layout_marginBottom="12dp" />

        <Button
            android:id="@+id/btnToggleNotificationMode"
            android:layout_width="match_parent"
            android:layout_height="42dp"
            android:text="Оповещение: [ ВЫКЛ ]"
            android:textColor="@color/text_white"
            android:backgroundTint="#21262D"
            android:textSize="12sp"
            android:layout_marginBottom="10dp" />

        <EditText
            android:id="@+id/etEditComment"
            android:layout_width="match_parent"
            android:layout_height="42dp"
            android:hint="Заметка к шагу"
            android:inputType="text"
            android:textColor="@color/text_white"
            android:textColorHint="@color/text_gray"
            android:background="@drawable/drag_handle_bg"
            android:padding="8dp"
            android:layout_marginBottom="14dp" />

        <LinearLayout
            android:id="@+id/layoutEditButtons"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal">

            <Button
                android:id="@+id/btnEditApply"
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="46dp"
                android:text="Сохранить"
                android:textColor="@color/text_white"
                android:backgroundTint="@color/accent_blue"
                android:textStyle="bold" />

            <View
                android:layout_width="8dp"
                android:layout_height="match_parent"/>

            <Button
                android:id="@+id/btnEditDelete"
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="46dp"
                android:text="Удалить"
                android:textColor="@color/red_close_text"
                android:backgroundTint="@color/red_close"
                android:textStyle="bold" />
        </LinearLayout>

        <Button
            android:id="@+id/btnEditClose"
            android:layout_width="match_parent"
            android:layout_height="42dp"
            android:text="Отмена"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/bg_dark_blue"
            android:layout_marginTop="10dp" />
    </LinearLayout>
</ScrollView>'''


# =============================================================================
# 4. EditActionDialog.kt (СЧИТЫВАНИЕ ТАЙМАУТА ПОИСКА)
# =============================================================================
EDIT_ACTION_DIALOG_KT = r'''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import com.example.autotap.playNotificationAlert
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class EditActionDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.floating_edit_dialog

    private var targetStepIndex: Int = -1
    private var etEditX: EditText? = null
    private var etEditY: EditText? = null
    private var etEditDelayMs: EditText? = null
    private var etEditSimilarity: EditText? = null
    private var etEditAiTimeout: EditText? = null
    private var btnToggleNotificationMode: Button? = null
    private var cbLoopUntilStopped: CheckBox? = null
    private var tvSelectedTemplatesSummary: TextView? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    fun setTargetStepIndex(index: Int) {
        this.targetStepIndex = index
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        etEditX = view.findViewByNames("etEditX") as? EditText
        etEditY = view.findViewByNames("etEditY") as? EditText
        etEditDelayMs = view.findViewByNames("etEditDelayMs") as? EditText
        etEditSimilarity = view.findViewByNames("etEditSimilarity") as? EditText
        etEditAiTimeout = view.findViewByNames("etEditAiTimeout") as? EditText
        btnToggleNotificationMode = view.findViewByNames("btnToggleNotificationMode") as? Button
        cbLoopUntilStopped = view.findViewByNames("cbLoopUntilStopped") as? CheckBox
        tvSelectedTemplatesSummary = view.findViewByNames("tvSelectedTemplatesSummary") as? TextView

        val actions = MyAutoClickService.instance?.actionsList ?: emptyList()
        val stepAction = if (targetStepIndex in actions.indices) {
            actions[targetStepIndex]
        } else actions.lastOrNull()

        if (stepAction != null) {
            bindActionToUI(stepAction)
        }

        view.bindClickByNames("btnOpenTemplatePicker") {
            val currentList = if (stepAction?.multiTemplateIndices?.isNotEmpty() == true) {
                stepAction.multiTemplateIndices
            } else listOf(stepAction?.selectedTemplateIndex ?: 0)

            overlayManager.templatePickerDialog.showPicker(currentList) { selected ->
                if (selected.isNotEmpty() && stepAction != null) {
                    stepAction.multiTemplateIndices = selected
                    stepAction.selectedTemplateIndex = selected[0]
                    updateSummaryText(selected)
                }
            }
        }

        view.bindClickByNames("btnToggleNotificationMode") {
            val action = stepAction ?: return@bindClickByNames
            action.notificationMode = (action.notificationMode + 1) % 4
            updateNotificationButtonText(action.notificationMode)
            context.playNotificationAlert(action.notificationMode)
        }

        view.bindClickByNames("btnEditApply", "btnSave") {
            val action = stepAction
            val screenSize = context.getRealScreenSize()
            if (action != null) {
                val inputX = etEditX?.text?.toString()?.toFloatOrNull()
                val inputY = etEditY?.text?.toString()?.toFloatOrNull()

                if (inputX != null) {
                    action.xNorm = if (inputX > 1.0f) (inputX / screenSize.x).coerceIn(0f, 1f) else inputX.coerceIn(0f, 1f)
                }
                if (inputY != null) {
                    action.yNorm = if (inputY > 1.0f) (inputY / screenSize.y).coerceIn(0f, 1f) else inputY.coerceIn(0f, 1f)
                }

                action.delay = etEditDelayMs?.text?.toString()?.toLongOrNull() ?: action.delay
                action.similarityPercent = etEditSimilarity?.text?.toString()?.toIntOrNull()?.coerceIn(10, 100) ?: action.similarityPercent
                action.aiTimeoutSeconds = etEditAiTimeout?.text?.toString()?.toFloatOrNull()?.coerceAtLeast(0.1f) ?: action.aiTimeoutSeconds
                action.loopUntilStopped = cbLoopUntilStopped?.isChecked ?: action.loopUntilStopped
            }
            logDiagnostic("SCRIPT", "Изменения сохранены: X=${action?.xNorm}, Y=${action?.yNorm}, Timeout=${action?.aiTimeoutSeconds}s")
            hide()
        }

        view.bindClickByNames("btnEditDelete", "btnDeleteAction") {
            val list = MyAutoClickService.instance?.actionsList
            if (list != null && list.isNotEmpty()) {
                val removeIdx = if (targetStepIndex in list.indices) targetStepIndex else list.size - 1
                list.removeAt(removeIdx)
            }
            hide()
        }

        view.bindClickByNames("btnEditClose", "btnCancel") {
            hide()
        }

        return view
    }

    private fun bindActionToUI(action: ActionConfig) {
        val screenSize = context.getRealScreenSize()
        etEditX?.setText((action.xNorm * screenSize.x).toInt().toString())
        etEditY?.setText((action.yNorm * screenSize.y).toInt().toString())

        etEditDelayMs?.setText(action.delay.toString())
        etEditSimilarity?.setText(action.similarityPercent.toString())
        etEditAiTimeout?.setText(action.aiTimeoutSeconds.toString())
        cbLoopUntilStopped?.isChecked = action.loopUntilStopped
        updateNotificationButtonText(action.notificationMode)

        val list = if (action.multiTemplateIndices.isNotEmpty()) action.multiTemplateIndices else listOf(action.selectedTemplateIndex)
        updateSummaryText(list)
    }

    private fun updateSummaryText(indices: List<Int>) {
        tvSelectedTemplatesSummary?.text = "Выбранные маски (${indices.size}): #" + indices.joinToString(", #")
    }

    private fun updateNotificationButtonText(mode: Int) {
        val label = when (mode) {
            1 -> "🔔 Оповещение: [ 📳 ВИБРО ]"
            2 -> "🔔 Оповещение: [ 🔊 ЗВУК ]"
            3 -> "🔔 Оповещение: [ 🔊+📳 ЗВУК + ВИБРО ]"
            else -> "🔔 Оповещение: [ ВЫКЛ ]"
        }
        btnToggleNotificationMode?.text = label
    }
}'''


# =============================================================================
# 5. CandidateSelectionOverlay.kt (ИНТЕРАКТИВНОЕ ПОДТВЕРЖДЕНИЕ ТАПОМ ПО ЭКРАНУ)
# =============================================================================
CANDIDATE_SELECTION_OVERLAY_KT = r'''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class CandidateSelectionOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.CANDIDATE_LAYER, OverlayPriority.HIGH) {

    private var activeCandidates = emptyList<MatchCandidate>()
    private var onCandidateConfirmed: ((MatchCandidate) -> Unit)? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.MATCH_PARENT
        gravity = Gravity.TOP or Gravity.START
    }

    override fun createView(): View {
        return BeaconRadarCustomView(context)
    }

    fun showRadarBeaconCandidates(
        candidates: List<MatchCandidate>,
        callback: (MatchCandidate) -> Unit
    ) {
        this.activeCandidates = candidates
        this.onCandidateConfirmed = callback
        show()
        (overlayView as? BeaconRadarCustomView)?.setCandidates(candidates)
    }

    private inner class BeaconRadarCustomView(context: Context) : View(context) {

        private var candidateList = emptyList<MatchCandidate>()
        private var pulseRadius = 0f
        private var isIncreasing = true
        private val mainHandler = Handler(Looper.getMainLooper())

        private val pulseRunnable = object : Runnable {
            override fun run() {
                if (isIncreasing) {
                    pulseRadius += 2.0f
                    if (pulseRadius >= 16f) isIncreasing = false
                } else {
                    pulseRadius -= 2.0f
                    if (pulseRadius <= 0f) isIncreasing = true
                }
                invalidate()
                mainHandler.postDelayed(this, 30L)
            }
        }

        private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#FF00F5D4")
            style = Paint.Style.STROKE
            strokeWidth = 6f
        }

        private val pulsePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#8000E5FF")
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 32f
            isFakeBoldText = true
        }

        init {
            mainHandler.post(pulseRunnable)
        }

        fun setCandidates(list: List<MatchCandidate>) {
            this.candidateList = list
            invalidate()
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            for ((index, c) in candidateList.withIndex()) {
                val bbox = c.boundingBox
                val rectF = RectF(bbox)

                // Пульсирующий неоновый маяк вокруг найденной цели
                canvas.drawRoundRect(rectF, 12f, 12f, borderPaint)

                val pulseRect = RectF(
                    rectF.left - pulseRadius,
                    rectF.top - pulseRadius,
                    rectF.right + pulseRadius,
                    rectF.bottom + pulseRadius
                )
                canvas.drawRoundRect(pulseRect, 16f, 16f, pulsePaint)

                val scorePercent = "${(c.score * 100).toInt()}%"
                canvas.drawText("🎯 #${index + 1} ($scorePercent)", rectF.left, (rectF.top - 12f).coerceAtLeast(40f), textPaint)
            }
        }

        override fun onTouchEvent(event: MotionEvent): Boolean {
            if (event.action == MotionEvent.ACTION_DOWN) {
                val touchX = event.rawX
                val touchY = event.rawY

                // Тап по маяку на экране = Подтверждение выбора цели!
                for (c in candidateList) {
                    if (c.boundingBox.contains(touchX.toInt(), touchY.toInt())) {
                        logDiagnostic("AI_SCANNER", "Пользователь подтвердил цель тапом по экрану: ${c.point}")
                        onCandidateConfirmed?.invoke(c)
                        hide()
                        return true
                    }
                }
            }
            return super.onTouchEvent(event)
        }

        override fun onDetachedFromWindow() {
            super.onDetachedFromWindow()
            mainHandler.removeCallbacks(pulseRunnable)
        }
    }
}'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v61 (OUTSIDE GRIP & RADAR BEACON)")
    print("=================================================================")

    tasks = [
        ("app/src/main/java/com/example/autotap/model/ActionConfig.kt", ACTION_CONFIG_KT),
        ("app/src/main/res/layout/floating_capture_frame.xml", CAPTURE_FRAME_XML),
        ("app/src/main/res/layout/floating_edit_dialog.xml", EDIT_DIALOG_XML),
        ("app/src/main/java/com/example/autotap/ui/overlays/EditActionDialog.kt", EDIT_ACTION_DIALOG_KT),
        ("app/src/main/java/com/example/autotap/ui/overlays/CandidateSelectionOverlay.kt", CANDIDATE_SELECTION_OVERLAY_KT),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ВСЕ УЛУЧШЕНИЯ УСПЕШНО ПРИМЕНЕНЫ К ПРОЕКТУ!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()