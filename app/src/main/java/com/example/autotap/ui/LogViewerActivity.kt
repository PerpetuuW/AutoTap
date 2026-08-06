package com.example.autotap.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError

class LogViewerActivity : AppCompatActivity() {

    private var logTextView: TextView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        try {
            setContentView(R.layout.dialog_logs)
            logDiagnostic("UI", "Экран логов надул оригинальный dialog_logs.xml")
        } catch (e: Exception) {
            logError("UI", "Ошибка установки setContentView(R.layout.dialog_logs)", e)
        }

        val root = window.decorView.findViewById<View>(android.R.id.content)

        logTextView = root.findViewByNames("tvLogsContent") as? TextView

        root.bindClickByNames("btnShareLogs") {
            shareLogFile()
        }

        root.bindClickByNames("btnClearLogs") {
            clearLogFile()
        }

        root.bindClickByNames("btnCloseLogs") {
            finish()
        }

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
            logDiagnostic("LOGS", "Лог-файл очищен по btnClearLogs.")
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
        } catch (e: Exception) {
            logError("LOGS", "Ошибка отправки файла логов", e)
        }
    }
}
