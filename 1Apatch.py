#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v53 - ACCURATE CROP, SHIFTING TOOLBARS & TEMPLATE PICKER DIALOG
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
# 1. NEW DIALOG LAYOUT: dialog_template_picker.xml
# =============================================================================
TEMPLATE_PICKER_DIALOG_XML = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="320dp"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:background="@drawable/panel_background"
    android:padding="16dp"
    android:elevation="22dp">

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="🖼 Выбор ИИ-Масок для Мультипоиска"
        android:textColor="#00F5D4"
        android:textSize="16sp"
        android:textStyle="bold"
        android:layout_marginBottom="12dp"/>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:layout_marginBottom="10dp">

        <Button
            android:id="@+id/btnSelectAllPicker"
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="38dp"
            android:minHeight="0dp"
            android:text="☑️ Выделить все"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/accent_blue"
            android:textSize="11sp"/>

        <View
            android:layout_width="8dp"
            android:layout_height="match_parent"/>

        <Button
            android:id="@+id/btnUnselectAllPicker"
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="38dp"
            android:minHeight="0dp"
            android:text="☐ Снять все"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/bg_dark_blue"
            android:textSize="11sp"/>
    </LinearLayout>

    <ScrollView
        android:overScrollMode="never"
        android:layout_width="match_parent"
        android:layout_height="240dp"
        android:background="@color/bg_dark_blue"
        android:padding="6dp"
        android:layout_marginBottom="14dp">

        <LinearLayout
            android:id="@+id/layoutTemplatesGrid"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"/>
    </ScrollView>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal">

        <Button
            android:id="@+id/btnApplyPicker"
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="44dp"
            android:text="✅ Применить"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/accent_blue"
            android:textStyle="bold"/>

        <View
            android:layout_width="8dp"
            android:layout_height="match_parent"/>

        <Button
            android:id="@+id/btnCancelPicker"
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="44dp"
            android:text="Отмена"
            android:textColor="#FFFFFF"
            android:backgroundTint="@color/bg_dark_blue"/>
    </LinearLayout>
</LinearLayout>'''


# =============================================================================
# 2. NEW KOTLIN DIALOG CLASS: TemplatePickerDialog.kt
# =============================================================================
TEMPLATE_PICKER_DIALOG_KT = '''package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class TemplatePickerDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_template_picker

    private var templatesContainer: LinearLayout? = null
    private val selectedIndices = mutableSetOf<Int>()
    private var onApplyCallback: ((List<Int>) -> Unit)? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    fun showPicker(currentIndices: List<Int>, callback: (List<Int>) -> Unit) {
        this.selectedIndices.clear()
        this.selectedIndices.addAll(currentIndices)
        this.onApplyCallback = callback
        show()
        populateGrid()
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        templatesContainer = view.findViewByNames("layoutTemplatesGrid") as? LinearLayout

        view.bindClickByNames("btnSelectAllPicker") {
            setAllChecked(true)
        }

        view.bindClickByNames("btnUnselectAllPicker") {
            setAllChecked(false)
        }

        view.bindClickByNames("btnApplyPicker") {
            val sorted = selectedIndices.sorted()
            logDiagnostic("AI_SCANNER", "Выбраны маски для мультипоиска: $sorted")
            onApplyCallback?.invoke(sorted)
            hide()
        }

        view.bindClickByNames("btnCancelPicker") {
            hide()
        }

        return view
    }

    private fun populateGrid() {
        val container = templatesContainer ?: return
        container.removeAllViews()

        val files = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") }
            ?.sortedBy { file ->
                file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: 0
            } ?: emptyList()

        if (files.isEmpty()) {
            val tv = TextView(context).apply {
                text = "Шаблонов пока нет. Вырежьте их прицелом 📷"
                setTextColor(Color.GRAY)
                gravity = Gravity.CENTER
                setPadding(16, 32, 16, 32)
            }
            container.addView(tv)
            return
        }

        for (file in files) {
            val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
            val row = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setBackgroundResource(R.drawable.drag_handle_bg)
                setPadding(12, 10, 12, 10)
                val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
                lp.setMargins(0, 0, 0, 8)
                layoutParams = lp
            }

            val cb = CheckBox(context).apply {
                isChecked = selectedIndices.contains(index)
                setOnCheckedChangeListener { _, isChecked ->
                    if (isChecked) selectedIndices.add(index) else selectedIndices.remove(index)
                }
            }

            val iv = ImageView(context).apply {
                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                if (bitmap != null) setImageBitmap(bitmap)
                layoutParams = LinearLayout.LayoutParams(60.dpToPx(context), 60.dpToPx(context)).apply {
                    setMargins(12, 0, 16, 0)
                }
                scaleType = ImageView.ScaleType.FIT_CENTER
                setBackgroundResource(R.drawable.border_capture_square)
            }

            val tv = TextView(context).apply {
                text = "ИИ-Маска #$index\nРазмер: ${file.length() / 1024} КБ"
                setTextColor(Color.WHITE)
                textSize = 13f
            }

            row.addView(cb)
            row.addView(iv)
            row.addView(tv)
            container.addView(row)
        }
    }

    private fun setAllChecked(checked: Boolean) {
        val container = templatesContainer ?: return
        selectedIndices.clear()

        val files = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") } ?: emptyArray()
        if (checked) {
            for (file in files) {
                val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
                selectedIndices.add(index)
            }
        }

        for (i in 0 until container.childCount) {
            val row = container.getChildAt(i) as? LinearLayout ?: continue
            val cb = row.getChildAt(0) as? CheckBox ?: continue
            cb.isChecked = checked
        }
    }

    private fun Int.dpToPx(context: Context): Int {
        return (this * context.resources.displayMetrics.density).toInt()
    }
}'''


# =============================================================================
# 3. EditActionDialog.kt (ВЫЗОВ ОКНА ВЫБОРА МАСОК)
# =============================================================================
EDIT_ACTION_DIALOG_KT = '''package com.example.autotap.ui.overlays

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
                action.loopUntilStopped = cbLoopUntilStopped?.isChecked ?: action.loopUntilStopped
            }
            logDiagnostic("SCRIPT", "Изменения сохранены: X=${action?.xNorm}, Y=${action?.yNorm}")
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
# 4. floating_edit_dialog.xml (КНОПКА ОТКРЫТИЯ ДИАЛОГА ВЫБОРА)
# =============================================================================
EDIT_DIALOG_XML = '''<?xml version="1.0" encoding="utf-8"?>
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
            android:text="✏️ Настройка шага сценария"
            android:textColor="#00F5D4"
            android:textSize="18sp"
            android:textStyle="bold"
            android:layout_marginBottom="12dp" />

        <!-- 1. ПОДПИСЬ: Координаты X и Y -->
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="📌 Экранные координаты клика (X и Y в пикселях):"
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
            android:text="⏱ Пауза перед кликом (миллисекунды):"
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

        <!-- 3. КНОПКА ОТКРЫТИЯ НОВОГО ДИАЛОГА ВЫБОРА МАСОК С ПРЕВЬЮ -->
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="🎯 Выбор ИИ-масок для мультипоиска:"
            android:textColor="#58A6FF"
            android:textSize="12sp"
            android:textStyle="bold"
            android:layout_marginBottom="4dp"/>

        <Button
            android:id="@+id/btnOpenTemplatePicker"
            android:layout_width="match_parent"
            android:layout_height="44dp"
            android:text="🖼 Открыть галерею масок с превью"
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
            android:layout_marginBottom="12dp"/>

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:gravity="center_vertical"
            android:layout_marginBottom="10dp">

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Точность совпадения %:"
                android:textColor="@color/text_gray"
                android:textSize="11sp"
                android:layout_marginEnd="8dp"/>

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

        <CheckBox
            android:id="@+id/cbLoopUntilStopped"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="🔁 Непрерывный мультипоиск до остановки"
            android:textColor="@color/text_white"
            android:textSize="12sp"
            android:layout_marginBottom="12dp" />

        <Button
            android:id="@+id/btnToggleNotificationMode"
            android:layout_width="match_parent"
            android:layout_height="42dp"
            android:text="🔔 Оповещение: [ ВЫКЛ ]"
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
                android:text="✅ Сохранить"
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
                android:text="🗑 Удалить"
                android:textColor="@color/text_white"
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
# 5. CaptureFrameOverlay.kt (ЗАХВАТ КООРДИНАТ ДО СКРЫТИЯ И СДВИГ ТУЛБАРОВ)
# =============================================================================
CAPTURE_FRAME_OVERLAY_KT = '''package com.example.autotap.ui.overlays

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
                // 1. ЗАХВАТЫВАЕМ ТОЧНЫЕ КООРДИНАТЫ РАМКИ ДО СКРЫТИЯ ОКНА
                val location = IntArray(2)
                square.getLocationOnScreen(location)
                val cropX = location[0]
                val cropY = location[1]
                val cropW = square.width
                val cropH = square.height

                // 2. Скрываем окно для чистого скриншота
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

        val topBar = topBarView ?: view
        val bottomBar = bottomBarView ?: view
        val square = captureSquareView ?: view

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

        // СДВИГАЕМ САМИ КНОПКИ ВЛЕВО/ВПРАВО У КРАЕВ ЭКРАНА (ПОЛЕ Х ОСТАЕТСЯ НА 0PX КРАЮ!)
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
# 6. OverlayManager.kt (РЕГИСТРАЦИЯ ТАМПЛЕЙТ-ПИКЕРА)
# =============================================================================
OVERLAY_MANAGER_KT = '''package com.example.autotap.ui.base

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.AddActionDialog
import com.example.autotap.ui.overlays.CandidateSelectionOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ClickVisualizerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.EditActionDialog
import com.example.autotap.ui.overlays.ExportImportDialog
import com.example.autotap.ui.overlays.FloatingStopButtonOverlay
import com.example.autotap.ui.overlays.GlobalSettingsDialog
import com.example.autotap.ui.overlays.InfoHelpDialog
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.MaskEditorDialog
import com.example.autotap.ui.overlays.PermissionsDialog
import com.example.autotap.ui.overlays.SaveRecordingDialog
import com.example.autotap.ui.overlays.ScriptsDialog
import com.example.autotap.ui.overlays.SearchAreaOverlay
import com.example.autotap.ui.overlays.TargetMarkerOverlay
import com.example.autotap.ui.overlays.TemplatePickerDialog
import com.example.autotap.ui.overlays.TemplatesManagerDialog
import com.example.autotap.ui.overlays.TutorialOverlay

class OverlayManager(val context: Context) {

    private val overlays = mutableMapOf<OverlayLayer, OverlayBase>()

    val controlPanel by lazy { ControlPanelOverlay(context, this) }
    val debuggerOverlay by lazy { ScenarioDebuggerOverlay(context, this) }
    val candidateOverlay by lazy { CandidateSelectionOverlay(context, this) }
    val joystickOverlay by lazy { JoystickOverlay(context, this) }
    val editActionDialog by lazy { EditActionDialog(context, this) }
    val captureFrameOverlay by lazy { CaptureFrameOverlay(context, this) }
    val scriptsDialog by lazy { ScriptsDialog(context, this) }
    val clickVisualizer by lazy { ClickVisualizerOverlay(context, this) }
    val tutorialOverlay by lazy { TutorialOverlay(context, this) }
    val infoHelpDialog by lazy { InfoHelpDialog(context, this) }
    val templatesManagerDialog by lazy { TemplatesManagerDialog(context, this) }
    val globalSettingsDialog by lazy { GlobalSettingsDialog(context, this) }
    val maskEditorDialog by lazy { MaskEditorDialog(context, this) }
    val floatingStopButton by lazy { FloatingStopButtonOverlay(context, this) }
    val addActionDialog by lazy { AddActionDialog(context, this) }
    val exportImportDialog by lazy { ExportImportDialog(context, this) }
    val permissionsDialog by lazy { PermissionsDialog(context, this) }
    val saveRecordingDialog by lazy { SaveRecordingDialog(context, this) }
    val searchAreaOverlay by lazy { SearchAreaOverlay(context, this) }
    val targetMarkerOverlay by lazy { TargetMarkerOverlay(context, this) }
    val templatePickerDialog by lazy { TemplatePickerDialog(context, this) }

    init {
        register(OverlayLayer.PANEL_LAYER, controlPanel)
        register(OverlayLayer.CAPTURE_LAYER, captureFrameOverlay)
        register(OverlayLayer.JOYSTICK_LAYER, joystickOverlay)
        register(OverlayLayer.DEBUG_LAYER, debuggerOverlay)
        register(OverlayLayer.TUTORIAL_LAYER, tutorialOverlay)
        register(OverlayLayer.DIALOG_LAYER, editActionDialog)
        register(OverlayLayer.SEARCH_AREA_LAYER, searchAreaOverlay)
        register(OverlayLayer.TARGET_LAYER, targetMarkerOverlay)
        register(OverlayLayer.STOP_BUTTON_LAYER, floatingStopButton)
        logDiagnostic("OVERLAY", "OverlayManager полностью инициализирован.")
    }

    fun register(layer: OverlayLayer, overlay: OverlayBase) {
        overlays[layer] = overlay
    }

    fun show(layer: OverlayLayer) {
        overlays[layer]?.show()
    }

    fun hide(layer: OverlayLayer) {
        overlays[layer]?.hide()
    }

    fun showControlPanel() {
        controlPanel.show()
    }

    fun hideControlPanel() {
        controlPanel.hide()
    }

    fun showFloatingStopButton() {
        floatingStopButton.show()
    }

    fun hideFloatingStopButton() {
        floatingStopButton.hide()
    }

    fun showClickVisualizer(x: Float, y: Float) {
        clickVisualizer.showClickAt(x, y)
    }

    fun setTouchable(layer: OverlayLayer, enabled: Boolean) {
        overlays[layer]?.setTouchable(enabled)
    }

    fun hideAll() {
        overlays.values.forEach { it.hide() }
    }

    fun onConfigurationChanged() {
        overlays.values.filter { it.isShowing }.forEach { overlay ->
            val lp = overlay.layoutParams ?: overlay.params
            val v = overlay.rootView ?: overlay.overlayView
            if (lp != null && v != null) {
                overlay.reboundToScreen(lp)
                try {
                    overlay.windowManager.updateViewLayout(v, lp)
                } catch (_: Exception) {}
            }
        }
        logDiagnostic("OVERLAY", "Автоматический пересчет позиций оверлеев при повороте экрана.")
    }
}'''


# =============================================================================
# 7. floating_control_panel.xml (ИКОНКА РАЗВОРОТА ≡ В БАББЛЕ)
# =============================================================================
CONTROL_PANEL_XML = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/layoutMainCard"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:background="@drawable/panel_background"
    android:padding="8dp"
    android:elevation="16dp">

    <!-- КНОПКА-БАББЛ СО ЗНАЧКОМ РАЗВОРОТА ≡ -->
    <ImageButton
        android:id="@+id/btnSingleBubble"
        android:layout_width="56dp"
        android:layout_height="56dp"
        android:src="@drawable/ic_menu"
        android:scaleType="centerInside"
        android:background="@drawable/handle_manipulator_bg"
        android:padding="12dp"
        android:visibility="gone"
        android:contentDescription="Expand Panel" />

    <!-- Строка 1: Главная панель -->
    <LinearLayout
        android:id="@+id/layoutMainRow"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:gravity="center_vertical">

        <TextView
            android:id="@+id/handleDrag"
            android:layout_width="26dp"
            android:layout_height="44dp"
            android:gravity="center"
            android:text="⁝⁝"
            android:textColor="#58A6FF"
            android:textSize="16sp"
            android:textStyle="bold"
            android:background="@drawable/drag_handle_bg"
            android:layout_marginEnd="6dp"/>

        <ImageButton
            android:id="@+id/btnPlay"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_play"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_primary"
            android:padding="10dp"
            android:contentDescription="Play"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnAdd"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_add"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Add"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnCapturePool"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_camera"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Capture"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnHelpTutorial"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_help"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="10dp"
            android:contentDescription="Help"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnToggleMenu"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_menu"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Menu"/>
    </LinearLayout>

    <!-- Строка 2: Доп. меню -->
    <LinearLayout
        android:id="@+id/layoutSubMenu"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:layout_marginTop="6dp"
        android:visibility="gone">

        <ImageButton
            android:id="@+id/btnClearAll"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_trash"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Clear"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnRecord"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_record"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Record"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnToggleJoystick"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/circle_target_end"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Joystick"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnLoadScript"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_folder"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Scripts"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnHideNumbers"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_eye"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_secondary"
            android:padding="10dp"
            android:contentDescription="Hide"
            android:layout_marginEnd="5dp"/>

        <ImageButton
            android:id="@+id/btnClose"
            android:layout_width="44dp"
            android:layout_height="44dp"
            android:src="@drawable/ic_close"
            android:scaleType="centerInside"
            android:background="@drawable/btn_premium_record"
            android:padding="10dp"
            android:contentDescription="Close"/>
    </LinearLayout>
</LinearLayout>'''


def execute_patch():
    print("=================================================================")
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v53 (ACCURATE CROP & SHIFTING TOOLBARS)")
    print("=================================================================")

    tasks = [
        ("app/src/main/res/layout/dialog_template_picker.xml", TEMPLATE_PICKER_DIALOG_XML),
        ("app/src/main/java/com/example/autotap/ui/overlays/TemplatePickerDialog.kt", TEMPLATE_PICKER_DIALOG_KT),
        ("app/src/main/res/layout/floating_edit_dialog.xml", EDIT_DIALOG_XML),
        ("app/src/main/java/com/example/autotap/ui/overlays/EditActionDialog.kt", EDIT_ACTION_DIALOG_KT),
        ("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", CAPTURE_FRAME_OVERLAY_KT),
        ("app/src/main/java/com/example/autotap/ui/base/OverlayManager.kt", OVERLAY_MANAGER_KT),
        ("app/src/main/res/layout/floating_control_panel.xml", CONTROL_PANEL_XML),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ВСЕ 5 ПОЖЕЛАНИЙ УСПЕШНО РЕАЛИЗОВАНЫ В КОДЕ!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()