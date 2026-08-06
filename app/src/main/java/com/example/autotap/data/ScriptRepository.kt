package com.example.autotap.data

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import java.io.File

class ScriptRepository(private val context: Context) {

    private val cache = mutableMapOf<String, List<ActionConfig>>()

    fun saveScript(name: String, actions: List<ActionConfig>): Boolean {
        return try {
            val file = File(context.filesDir, "$name.json")
            val serialized = actions.joinToString(separator = "\n") { action ->
                "${action.type.name};${action.xNorm};${action.yNorm};${action.endXNorm};${action.endYNorm};${action.delay};${action.holdDuration}"
            }
            file.writeText(serialized)
            cache[name] = actions.toList()
            logDiagnostic("SCRIPT", "Сценарий '$name' успешно сохранен (${actions.size} шагов).")
            true
        } catch (e: Exception) {
            logError("SCRIPT", "Ошибка сохранения сценария '$name'", e)
            false
        }
    }

    fun loadScript(name: String): List<ActionConfig> {
        if (cache.containsKey(name)) {
            val cached = cache[name] ?: emptyList()
            logDiagnostic("SCRIPT", "Сценарий '$name' загружен из кэша.")
            return cached
        }

        return try {
            val file = File(context.filesDir, "$name.json")
            if (!file.exists()) {
                logDiagnostic("SCRIPT", "Файл сценария '$name' не найден.")
                return emptyList()
            }
            val lines = file.readLines()
            val list = mutableListOf<ActionConfig>()
            for (line in lines) {
                if (line.isBlank()) continue
                val parts = line.split(";")
                if (parts.isNotEmpty()) {
                    val config = ActionConfig(
                        xNorm = parts.getOrNull(1)?.toFloatOrNull() ?: 0.5f,
                        yNorm = parts.getOrNull(2)?.toFloatOrNull() ?: 0.5f,
                        endXNorm = parts.getOrNull(3)?.toFloatOrNull() ?: 0.5f,
                        endYNorm = parts.getOrNull(4)?.toFloatOrNull() ?: 0.5f,
                        delay = parts.getOrNull(5)?.toLongOrNull() ?: 500L,
                        holdDuration = parts.getOrNull(6)?.toLongOrNull() ?: 100L
                    )
                    list.add(config)
                }
            }
            cache[name] = list
            logDiagnostic("SCRIPT", "Сценарий '$name' загружен из файла (${list.size} шагов).")
            list
        } catch (e: Exception) {
            logError("SCRIPT", "Ошибка загрузки сценария '$name'", e)
            emptyList()
        }
    }
}
