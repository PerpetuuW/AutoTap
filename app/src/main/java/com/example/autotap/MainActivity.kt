package com.example.autotap

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.LogViewerActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        StructuredLogger.init(this)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        val statusText = TextView(this).apply {
            text = "AutoTap v35 System Status"
            textSize = 18f
            setPadding(0, 0, 0, 16)
        }
        layout.addView(statusText)

        val btnAccessibility = Button(this).apply {
            text = "Включить Accessibility Service"
            setOnClickListener {
                try {
                    startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                } catch (e: Exception) {
                    logError("UI", "Ошибка перехода в настройки Accessibility", e)
                }
            }
        }
        layout.addView(btnAccessibility)

        val btnOverlay = Button(this).apply {
            text = "Запустить Overlay Панель"
            setOnClickListener {
                val service = MyAutoClickService.instance
                if (service != null) {
                    service.showControlPanel()
                    logDiagnostic("UI", "Запрос показа Control Panel из MainActivity")
                } else {
                    logError("UI", "MyAutoClickService не запущен или не активен!", null)
                }
            }
        }
        layout.addView(btnOverlay)

        val btnLogs = Button(this).apply {
            text = "Просмотр Диагностических Логов"
            setOnClickListener {
                try {
                    startActivity(Intent(this@MainActivity, LogViewerActivity::class.java))
                } catch (e: Exception) {
                    logError("UI", "Ошибка открытия LogViewerActivity", e)
                }
            }
        }
        layout.addView(btnLogs)

        setContentView(layout)
        logDiagnostic("UI", "MainActivity успешно инициализирована.")
    }
}
