package com.example.autotap.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError

class LogViewerActivity : AppCompatActivity() {

    private var logTextView: TextView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 24, 24, 24)
        }

        val title = TextView(this).apply {
            text = "Просмотр диагностических логов AutoTap"
            textSize = 18f
            setPadding(0, 0, 0, 16)
        }
        root.addView(title)

        val btnContainer = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 0, 0, 16)
        }

        val btnShare = Button(this).apply {
            text = "Поделиться"
            setOnClickListener {
                shareLogFile()
            }
        }
        btnContainer.addView(btnShare)

        val btnClear = Button(this).apply {
            text = "Очистить"
            setOnClickListener {
                clearLogFile()
            }
        }
        btnContainer.addView(btnClear)

        root.addView(btnContainer)

        val scrollView = ScrollView(this)
        val tv = TextView(this).apply {
            textSize = 12f
            setPadding(8, 8, 8, 8)
        }
        logTextView = tv
        scrollView.addView(tv)
        root.addView(scrollView)

        setContentView(root)
        refreshLogs()
    }

    private fun refreshLogs() {
        val file = StructuredLogger.getLogFile()
        if (file != null && file.exists()) {
            val content = file.readText()
            logTextView?.text = if (content.isBlank()) "Лог-файл пуст." else content
        } else {
            logTextView?.text = "Лог-файл еще не создан."
        }
    }

    private fun clearLogFile() {
        val file = StructuredLogger.getLogFile()
        if (file != null && file.exists()) {
            file.writeText("")
            logDiagnostic("LOGS", "Лог-файл успешно очищен пользователем.")
        }
        refreshLogs()
    }

    private fun shareLogFile() {
        val file = StructuredLogger.getLogFile() ?: return
        if (!file.exists()) return

        try {
            val uri: Uri = FileProvider.getUriForFile(
                this,
                "$packageName.fileprovider",
                file
            )
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(intent, "Поделиться error_log.txt"))
            logDiagnostic("LOGS", "Отправлен Intent обмена файлом логов.")
        } catch (e: Exception) {
            logError("LOGS", "Ошибка отправки файла логов", e)
        }
    }
}
