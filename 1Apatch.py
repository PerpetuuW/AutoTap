#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re

class PrecisionPatcher:
    """
    Движок точечного патчинга v40: проверяет баланс скобок
    и атомарно обновляет файлы проекта.
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
# 1. MAIN ACTIVITY С ПОДКАЗКОЙ ПРО "В САМОМ НИЗУ ЭКРАНА"
# ==============================================================================
MAIN_ACTIVITY_CONTENT = """package com.example.autotap

import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.LogViewerActivity

class MainActivity : AppCompatActivity() {

    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository
    lateinit var actionEditorEngine: ActionEditorEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        StructuredLogger.init(this)

        initRepositories()
        initEngines()

        try {
            setContentView(R.layout.activity_main)
            logDiagnostic("UI", "Главное меню успешно надуло activity_main.xml")
        } catch (e: Exception) {
            logError("UI", "Ошибка установки setContentView(R.layout.activity_main)", e)
        }

        val root = window.decorView.findViewById<View>(android.R.id.content)

        val versionName = try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: getString(R.string.app_version)
        } catch (_: Exception) {
            getString(R.string.app_version)
        }

        (root.findViewByNames("tvVersion") as? TextView)?.text = versionName
        (root.findViewByNames("tvSubTitle") as? TextView)?.text = "Комплекс Автоматизации и ИИ Поиска"

        root.bindClickByNames("btnStartPanel") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.showControlPanel()
                logDiagnostic("UI", "Запуск панели оверлеев.")
            } else {
                Toast.makeText(this, "Сначала включите Раздел 'Спец. возможности'!", Toast.LENGTH_LONG).show()
                logError("UI", "MyAutoClickService не запущен!", null)
            }
        }

        root.bindClickByNames("btnAccessibility") {
            try {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                logDiagnostic("UI", "Переход в системное меню Спец. возможности.")
            } catch (e: Exception) {
                logError("UI", "Ошибка перехода в Спец. возможности", e)
            }
        }

        root.bindClickByNames("btnOverlay") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this@MainActivity)) {
                try {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivity(intent)
                    logDiagnostic("UI", "Запрос разрешения Поверх других приложений.")
                } catch (e: Exception) {
                    logError("UI", "Ошибка запроса разрешения Поверх других приложений", e)
                }
            } else {
                Toast.makeText(this, "Разрешение 'Поверх других приложений' уже предоставлено!", Toast.LENGTH_SHORT).show()
            }
        }

        root.bindClickByNames("btnAppDetails", "btnPermissionsHelp") {
            openRestrictedSettingsMenu()
        }

        root.bindClickByNames("btnShowLogs") {
            try {
                startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
            } catch (e: Exception) {
                logError("UI", "Ошибка открытия LogViewerActivity", e)
            }
        }

        root.bindClickByNames("btnInfoHelp") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.infoHelpDialog.show()
            }
        }

        root.bindClickByNames("btnManageTemplates") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.templatesManagerDialog.show()
            }
        }

        root.bindClickByNames("btnExport", "btnImport") {
            val service = MyAutoClickService.instance
            if (service != null) {
                service.overlayManager.exportImportDialog.show()
            }
        }

        updateUIStatusIndicators()
    }

    override fun onResume() {
        super.onResume()
        updateUIStatusIndicators()
    }

    private fun openRestrictedSettingsMenu() {
        try {
            val intent = Intent(
                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:$packageName")
            )
            startActivity(intent)
            Toast.makeText(
                this,
                "Найдите в самом низу экрана (или в меню 3 точек вверху) пункт 'Разрешить ограниченные настройки' и включите его",
                Toast.LENGTH_LONG
            ).show()
            logDiagnostic("UI", "Открыто меню снятия ограничений Restricted Settings.")
        } catch (e: Exception) {
            logError("UI", "Ошибка открытия настроек приложения", e)
        }
    }

    private fun updateUIStatusIndicators() {
        val root = window.decorView.findViewById<View>(android.R.id.content)
        val isServiceActive = MyAutoClickService.instance != null
        val hasOverlay = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) Settings.canDrawOverlays(this) else true

        (root.findViewByNames("btnAccessibility") as? Button)?.apply {
            text = if (isServiceActive) "1. Спец. возможности: [ ВКЛ ]" else "1. Спец. возможности: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (isServiceActive) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnOverlay") as? Button)?.apply {
            text = if (hasOverlay) "2. Поверх других приложений: [ ВКЛ ]" else "2. Поверх других приложений: [ ВЫКЛ ]"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(if (hasOverlay) Color.parseColor("#00E676") else Color.parseColor("#FF5252"))
        }

        (root.findViewByNames("btnPermissionsHelp", "btnAppDetails") as? Button)?.apply {
            text = "3. Ограниченные настройки (в самом низу)"
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
        }
    }

    private fun initRepositories() {
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)
    }

    private fun initEngines() {
        actionEditorEngine = ActionEditorEngine()
    }
}
"""


# ==============================================================================
# 2. ACTIVITY MAIN XML С ТЕКСТОМ "В САМОМ НИЗУ"
# ==============================================================================
ACTIVITY_MAIN_XML_CONTENT = """<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@color/bg_dark_blue"
    android:fitsSystemWindows="true"
    android:fillViewport="true">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:paddingStart="16dp"
        android:paddingEnd="16dp"
        android:paddingTop="24dp"
        android:paddingBottom="16dp">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:gravity="center"
            android:background="@drawable/panel_background"
            android:paddingTop="16dp"
            android:paddingBottom="16dp"
            android:paddingStart="12dp"
            android:paddingEnd="12dp"
            android:layout_marginBottom="16dp">

            <TextView
                android:id="@+id/tvTitle"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="AutoTap Premium"
                android:textColor="#00F5D4"
                android:textSize="22sp"
                android:textStyle="bold"
                android:gravity="center"
                android:singleLine="true"
                android:maxLines="1"
                android:ellipsize="end" />

            <TextView
                android:id="@+id/tvSubTitle"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Комплекс Автоматизации и ИИ Поиска"
                android:textColor="@color/text_gray"
                android:textSize="11sp"
                android:gravity="center"
                android:layout_marginTop="4dp" />

            <TextView
                android:id="@+id/tvVersion"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="v40.0.0-PRO"
                android:textColor="@color/accent_blue"
                android:textSize="11sp"
                android:textStyle="bold"
                android:gravity="center"
                android:layout_marginTop="4dp" />
        </LinearLayout>

        <!-- Секция 1: Настройки системных разрешений -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:background="@drawable/panel_background"
            android:padding="14dp"
            android:layout_marginBottom="12dp">

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="⚙ Настройка системных разрешений"
                android:textColor="#58A6FF"
                android:textSize="13sp"
                android:textStyle="bold"
                android:layout_marginBottom="10dp"/>

            <Button
                android:id="@+id/btnAccessibility"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:minHeight="48dp"
                android:text="1. Спец. возможности (Включить AutoTap)"
                android:textColor="@color/text_white"
                android:backgroundTint="#21262D"
                android:textSize="12sp"
                android:padding="8dp"
                android:gravity="center"
                android:layout_marginBottom="8dp"/>

            <Button
                android:id="@+id/btnOverlay"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:minHeight="48dp"
                android:text="2. Поверх других приложений"
                android:textColor="@color/text_white"
                android:backgroundTint="#21262D"
                android:textSize="12sp"
                android:padding="8dp"
                android:gravity="center"
                android:layout_marginBottom="8dp"/>

            <Button
                android:id="@+id/btnAppDetails"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:minHeight="48dp"
                android:text="3. Ограниченные настройки (в самом низу / 3 точки)"
                android:textColor="@color/text_white"
                android:backgroundTint="#21262D"
                android:textSize="11sp"
                android:padding="8dp"
                android:gravity="center"/>
        </LinearLayout>

        <!-- Секция 2: Управление данными -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:background="@drawable/panel_background"
            android:padding="14dp"
            android:layout_marginBottom="12dp">

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="📁 Управление шаблонами и данными"
                android:textColor="#58A6FF"
                android:textSize="13sp"
                android:textStyle="bold"
                android:layout_marginBottom="10dp"/>

            <Button
                android:id="@+id/btnManageTemplates"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:minHeight="46dp"
                android:text="Редактирование и менеджер ИИ-шаблонов"
                android:textColor="@color/text_white"
                android:backgroundTint="#21262D"
                android:textSize="11sp"
                android:padding="8dp"
                android:gravity="center"
                android:layout_marginBottom="8dp"/>

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal">

                <Button
                    android:id="@+id/btnExport"
                    android:layout_width="0dp"
                    android:layout_weight="1"
                    android:layout_height="wrap_content"
                    android:minHeight="46dp"
                    android:text="📤 Экспорт"
                    android:textColor="@color/text_white"
                    android:backgroundTint="#21262D"
                    android:textSize="11sp"
                    android:padding="4dp"
                    android:gravity="center"/>

                <View
                    android:layout_width="8dp"
                    android:layout_height="match_parent"/>

                <Button
                    android:id="@+id/btnImport"
                    android:layout_width="0dp"
                    android:layout_weight="1"
                    android:layout_height="wrap_content"
                    android:minHeight="46dp"
                    android:text="📥 Импорт"
                    android:textColor="@color/text_white"
                    android:backgroundTint="#21262D"
                    android:textSize="11sp"
                    android:padding="4dp"
                    android:gravity="center"/>
            </LinearLayout>
        </LinearLayout>

        <!-- Секция 3: Инфо и Логи -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:background="@drawable/panel_background"
            android:padding="14dp"
            android:layout_marginBottom="16dp">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:layout_marginBottom="8dp">

                <Button
                    android:id="@+id/btnPermissionsHelp"
                    android:layout_width="0dp"
                    android:layout_weight="1"
                    android:layout_height="wrap_content"
                    android:minHeight="44dp"
                    android:text="О разрешениях"
                    android:textColor="@color/text_white"
                    android:backgroundTint="#21262D"
                    android:textSize="11sp"
                    android:padding="4dp"
                    android:gravity="center"/>

                <View
                    android:layout_width="8dp"
                    android:layout_height="match_parent"/>

                <Button
                    android:id="@+id/btnInfoHelp"
                    android:layout_width="0dp"
                    android:layout_weight="1"
                    android:layout_height="wrap_content"
                    android:minHeight="44dp"
                    android:text="Справка v40 PRO"
                    android:textColor="@color/text_white"
                    android:backgroundTint="#21262D"
                    android:textSize="11sp"
                    android:padding="4dp"
                    android:gravity="center"/>
            </LinearLayout>

            <Button
                android:id="@+id/btnShowLogs"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:minHeight="44dp"
                android:text="Просмотр логов работы и ошибок"
                android:textColor="@color/text_white"
                android:backgroundTint="#21262D"
                android:textSize="11sp"
                android:padding="4dp"
                android:gravity="center"/>
        </LinearLayout>

        <Button
            android:id="@+id/btnStartPanel"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:minHeight="56dp"
            android:text="🚀 ЗАПУСТИТЬ ПАНЕЛЬ КЛИКЕРА"
            android:textColor="@color/text_white"
            android:backgroundTint="@color/accent_blue"
            android:textSize="14sp"
            android:textStyle="bold"
            android:padding="10dp"
            android:gravity="center"/>
    </LinearLayout>
</ScrollView>
"""


def main():
    base_dir = os.getcwd()
    print("=== ОБНОВЛЕНИЕ ИНСТРУКЦИИ ОГРАНИЧЕННЫХ НАСТРОЕК (В САМОМ НИЗУ ЭКРАНА) ===")

    files_map = {
        "app/src/main/java/com/example/autotap/MainActivity.kt": MAIN_ACTIVITY_CONTENT,
        "app/src/main/res/layout/activity_main.xml": ACTIVITY_MAIN_XML_CONTENT,
    }

    try:
        for rel_path, content in files_map.items():
            full_path = os.path.join(base_dir, rel_path)
            patcher = PrecisionPatcher(full_path, content)
            patcher.apply()

        print("🟢 ВЁРСТКА И ТЕКСТ ПОДСКАЗОК УСПЕШНО ОБНОВЛЕНЫ!")
    except Exception as e:
        print(f"❌ ОШИБКА ПАТЧИНГА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()