#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re

class PrecisionPatcher:
    """
    Движок патчинга v40 Precision Architecture (Pro Features Edition).
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
        print(f"🟢 PRO FEATURE PATCHED: {os.path.basename(self.file_path)}")


# ==============================================================================
# 1. QUICK TILE SERVICE (БЫСТРАЯ ПЛИТКА В ШТОРКЕ ANDROID)
# ==============================================================================
QUICK_TILE_SERVICE_CONTENT = """package com.example.autotap.service

import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import android.widget.Toast
import androidx.annotation.RequiresApi
import com.example.autotap.MainActivity
import com.example.autotap.MyAutoClickService

@RequiresApi(Build.VERSION_CODES.N)
class QuickTileService : TileService() {

    override fun onStartListening() {
        super.onStartListening()
        updateTileState()
    }

    override fun onClick() {
        super.onClick()
        val svc = MyAutoClickService.instance
        if (svc != null) {
            svc.showControlPanel()
            Toast.makeText(this, "Панель AutoTap запущен!", Toast.LENGTH_SHORT).show()
        } else {
            val intent = Intent(this, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivityAndCollapse(intent)
        }
        updateTileState()
    }

    private fun updateTileState() {
        val tile = qsTile ?: return
        val isActive = MyAutoClickService.instance != null
        tile.state = if (isActive) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        tile.label = if (isActive) "AutoTap: ВКЛ" else "AutoTap: ВЫКЛ"
        tile.updateTile()
    }
}
"""


# ==============================================================================
# 2. HEATMAP GENERATOR (ТЕПЛОВАЯ КАРТА ПОИСКА ИИ)
# ==============================================================================
HEATMAP_GENERATOR_CONTENT = """package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint

class HeatmapGenerator {

    fun generateHeatmap(frame: Bitmap, candidates: List<MatchCandidate>): Bitmap {
        val heatmap = Bitmap.createBitmap(frame.width, frame.height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(heatmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
        }

        for (c in candidates) {
            val score = c.score
            paint.color = when {
                score >= 0.85f -> Color.argb(140, 0, 245, 212)
                score >= 0.70f -> Color.argb(110, 255, 183, 3)
                else -> Color.argb(80, 240, 68, 56)
            }
            canvas.drawRect(c.boundingBox, paint)
        }
        return heatmap
    }
}
"""


# ==============================================================================
# 3. AUTO TUNING ENGINE (АДАПТИВНЫЙ АВТО-ПОДБОР ПОРОГА)
# ==============================================================================
AUTO_TUNING_ENGINE_CONTENT = """package com.example.autotap.engine.ai

import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig

class AutoTuningEngine {

    fun adaptivelyTuneThreshold(
        action: ActionConfig,
        candidates: List<MatchCandidate>,
        scanFunction: (Float) -> List<MatchCandidate>
    ): List<MatchCandidate> {
        if (candidates.isNotEmpty()) return candidates
        if (!action.autoTuningMode) return candidates

        val currentThreshold = action.similarityPercent / 100f
        val softThreshold = (currentThreshold - 0.10f).coerceAtLeast(0.50f)

        logDiagnostic("AI_SCANNER", "AutoTuning: первая попытка не дала результатов. Адаптивное снижение порога до ${(softThreshold * 100).toInt()}%...")

        val softCandidates = scanFunction(softThreshold)
        if (softCandidates.isNotEmpty()) {
            val best = softCandidates.maxByOrNull { it.score }
            logDiagnostic("AI_SCANNER", "AutoTuning: цель успешно найдена адаптивно с уверенностью ${((best?.score ?: 0f) * 100).toInt()}%!")
        }
        return softCandidates
    }
}
"""


# ==============================================================================
# 4. SCENARIO DEBUGGER OVERLAY (ОТОБРАЖЕНИЕ HEATMAP КАРТЫ)
# ==============================================================================
SCENARIO_DEBUGGER_OVERLAY_CONTENT = """package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.findViewByNames
import com.example.autotap.logAppEvent
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null
    private var tvCandidatePercentView: TextView? = null
    private var viewCandidateBorderView: View? = null
    private var ivHeatmap: ImageView? = null

    init {
        width = 600
        height = 400
        gravity = Gravity.TOP or Gravity.END
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#AA000000"))
            setPadding(16, 16, 16, 16)

            val tv = TextView(context).apply {
                text = "Scenario Debugger: Готов"
                setTextColor(Color.GREEN)
                textSize = 14f
            }
            statusText = tv
            addView(tv)

            val img = ImageView(context).apply {
                visibility = View.GONE
            }
            ivHeatmap = img
            addView(img, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                200
            ))
        }

        val inflater = LayoutInflater.from(context)
        try {
            val calibBox = inflater.inflate(R.layout.floating_calibration_box, null)
            tvCandidatePercentView = calibBox.findViewByNames("tvCandidatePercent") as? TextView
            viewCandidateBorderView = calibBox.findViewByNames("viewCandidateBorder")
            root.addView(calibBox)
        } catch (_: Exception) {}

        return root
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        val scorePercent = if (candidates.isNotEmpty()) "${(candidates.first().score * 100).toInt()}%" else "0%"
        statusText?.text = "Кандидатов найдено: ${candidates.size} ($scorePercent)"
        tvCandidatePercentView?.text = scorePercent
        logAppEvent("AI_SCANNER", "Debugger: кандидатов ${candidates.size}")
    }

    fun showHeatmap(heatmap: Bitmap) {
        ivHeatmap?.setImageBitmap(heatmap)
        ivHeatmap?.visibility = View.VISIBLE
    }

    fun showNoMatch() {
        statusText?.text = "NO MATCH: Совпадения не найдены"
        tvCandidatePercentView?.text = "0%"
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")
    }
}
"""


# ==============================================================================
# 5. MANIFEST (РЕГИСТРАЦИЯ QUICK TILE SERVICE)
# ==============================================================================
MANIFEST_CONTENT = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AutoTap">

        <activity
            android:name="com.example.autotap.MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name="com.example.autotap.ui.LogViewerActivity"
            android:exported="false"
            android:label="Диагностика и Логи" />

        <service
            android:name="com.example.autotap.MyAutoClickService"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>

        <service
            android:name="com.example.autotap.service.QuickTileService"
            android:icon="@drawable/ic_play"
            android:label="AutoTap"
            android:permission="android.permission.BIND_QUICK_SETTINGS_TILE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.service.quicksettings.action.QS_TILE" />
            </intent-filter>
        </service>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>

    </application>

</manifest>
"""


def main():
    base_dir = os.getcwd()
    print("=== ЗАПУСК ПАТЧИНГА PRO ФИЧ (Quick Tile, Heatmap, Auto-Tuning) ===")

    files_map = {
        "app/src/main/java/com/example/autotap/service/QuickTileService.kt": QUICK_TILE_SERVICE_CONTENT,
        "app/src/main/java/com/example/autotap/engine/ai/HeatmapGenerator.kt": HEATMAP_GENERATOR_CONTENT,
        "app/src/main/java/com/example/autotap/engine/ai/AutoTuningEngine.kt": AUTO_TUNING_ENGINE_CONTENT,
        "app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt": SCENARIO_DEBUGGER_OVERLAY_CONTENT,
        "app/src/main/AndroidManifest.xml": MANIFEST_CONTENT,
    }

    try:
        for rel_path, content in files_map.items():
            full_path = os.path.join(base_dir, rel_path)
            patcher = PrecisionPatcher(full_path, content)
            patcher.apply()

        print("\n🏆 ВСЕ 3 ПРЕМИУМ-ФИЧИ УСПЕШНО ВНЕДРЕНЫ В КОД!")
        print("🟢 Плитка в шторке, Тепловая карта и Адаптивный подбор порога готовы.")
    except Exception as e:
        print(f"❌ ОШИБКА ПАТЧИНГА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()