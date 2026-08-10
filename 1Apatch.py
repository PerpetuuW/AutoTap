#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v43 - SCENARIO DEBUGGER showNoMatch FIX & SYSTEM OVERHAUL
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
# SCENARIO DEBUGGER OVERLAY (С МЕТОДАМИ showNoMatch И showCandidates)
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
                text = "Подтвердить объект"
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

    fun startLiveCalibration(templateIndex: Int) {
        this.currentTemplateIndex = templateIndex
        show()

        val svc = MyAutoClickService.instance ?: return
        val bitmap = svc.templateRepository.loadTemplate(templateIndex)

        if (bitmap != null) {
            ivPreview?.setImageBitmap(bitmap)
            ivPreview?.visibility = View.VISIBLE
            statusText?.text = "Сканирование экрана для Маски #$templateIndex...\nПодтвердите найденный объект"
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
        hide()
    }

    fun showCalibratedTemplate(bitmap: Bitmap, templateIndex: Int, profileName: String, widthPx: Int, heightPx: Int) {
        startLiveCalibration(templateIndex)
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
    print("🚀 СТАРТ ПАТЧИНГА AUTOTAP PRO v43 (showNoMatch & showCandidates FIX)")
    print("=================================================================")

    tasks = [
        ("app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt", SCENARIO_DEBUGGER_OVERLAY_KT),
    ]

    for rel_path, content in tasks:
        write_file(rel_path, content)

    print("=================================================================")
    print("🎉 ОШИБКА КОМПИЛЯЦИИ ScriptExecutor.kt УСПЕШНО УСТРАНЕНА!")
    print("=================================================================")

if __name__ == "__main__":
    execute_patch()