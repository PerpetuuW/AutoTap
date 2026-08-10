package com.example.autotap.logger

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object StructuredLogger {
    private const val MAX_LOG_SIZE = 524288L // 512 KB
    private var logFile: File? = null

    fun init(context: Context) {
        val dir = context.filesDir
        logFile = File(dir, "error_log.txt")
        rotateLogIfNeeded()
        logDiagnostic("SYSTEM", "StructuredLogger успешно инициализирован. Путь: " + (logFile?.absolutePath ?: "null"))
    }

    @Synchronized
    fun logDiagnostic(category: String, message: String) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        val formatted = "[" + timestamp + "] [" + category + "] " + message + "\n"
        println(formatted)
        appendToLogFile(formatted)
    }

    @Synchronized
    fun logError(category: String, message: String, throwable: Throwable? = null) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        val errText = if (throwable != null) "\nСтек ошибки: " + throwable.stackTraceToString() else ""
        val formatted = "[" + timestamp + "] [ERROR] [" + category + "] " + message + errText + "\n"
        System.err.println(formatted)
        appendToLogFile(formatted)
    }

    private fun appendToLogFile(text: String) {
        val file = logFile ?: return
        try {
            rotateLogIfNeeded()
            file.appendText(text)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun rotateLogIfNeeded() {
        val file = logFile ?: return
        try {
            if (file.exists() && file.length() > MAX_LOG_SIZE) {
                val content = file.readText()
                val halfIndex = content.length / 2
                val trimmedContent = "...[АВТО-ОЧИСТКА СТАРЫХ ЛОГОВ]...\n" + content.substring(halfIndex)
                file.writeText(trimmedContent)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun getLogFile(): File? = logFile
}

fun logError(category: String, message: String, throwable: Throwable? = null) {
    StructuredLogger.logError(category, message, throwable)
}

fun logDiagnostic(category: String, message: String) {
    StructuredLogger.logDiagnostic(category, message)
}
