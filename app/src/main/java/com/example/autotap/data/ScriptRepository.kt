package com.example.autotap.data

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.ConcurrentHashMap

class ScriptRepository(private val context: Context) {

    private val cache = ConcurrentHashMap<String, List<ActionConfig>>()
    var currentMetadata: ScriptMetadata? = null

    fun saveScript(name: String, actions: List<ActionConfig>, metadata: ScriptMetadata = ScriptMetadata(name = name, stepCount = actions.size)): Boolean {
        return try {
            val file = File(context.filesDir, "$name.json")
            val rootObj = JSONObject()

            rootObj.put("metadata", metadata.toJson())

            val actionsArray = JSONArray()
            for (action in actions) {
                val actionObj = JSONObject().apply {
                    put("type", action.type.name)
                    put("xNorm", action.xNorm)
                    put("yNorm", action.yNorm)
                    put("endXNorm", action.endXNorm)
                    put("endYNorm", action.endYNorm)
                    put("delay", action.delay)
                    put("holdDuration", action.holdDuration)
                    put("similarityPercent", action.similarityPercent)
                    put("aiTimeoutSeconds", action.aiTimeoutSeconds)
                    put("selectedTemplateIndex", action.selectedTemplateIndex)
                    put("customSearchArea", action.customSearchArea)
                    put("searchAreaX", action.searchAreaX)
                    put("searchAreaY", action.searchAreaY)
                    put("searchAreaW", action.searchAreaW)
                    put("searchAreaH", action.searchAreaH)
                }
                actionsArray.put(actionObj)
            }
            rootObj.put("actions", actionsArray)

            file.writeText(rootObj.toString(2))
            cache[name] = actions.toList()
            currentMetadata = metadata
            logDiagnostic("SCRIPT", "Сценарий '$name' успешно сохранен в JSON (${actions.size} шагов).")
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
            val content = file.readText()
            val list = mutableListOf<ActionConfig>()

            if (content.trim().startsWith("{")) {
                val rootObj = JSONObject(content)
                if (rootObj.has("metadata")) {
                    currentMetadata = ScriptMetadata.fromJson(rootObj.getJSONObject("metadata"))
                }
                val actionsArray = rootObj.optJSONArray("actions") ?: JSONArray()
                for (i in 0 until actionsArray.length()) {
                    val obj = actionsArray.getJSONObject(i)
                    val config = ActionConfig(
                        xNorm = obj.optDouble("xNorm", 0.5).toFloat(),
                        yNorm = obj.optDouble("yNorm", 0.5).toFloat(),
                        endXNorm = obj.optDouble("endXNorm", 0.5).toFloat(),
                        endYNorm = obj.optDouble("endYNorm", 0.5).toFloat(),
                        delay = obj.optLong("delay", 500L),
                        holdDuration = obj.optLong("holdDuration", 100L),
                        similarityPercent = obj.optInt("similarityPercent", 85),
                        aiTimeoutSeconds = obj.optDouble("aiTimeoutSeconds", 5.0).toFloat(),
                        selectedTemplateIndex = obj.optInt("selectedTemplateIndex", 0),
                        customSearchArea = obj.optBoolean("customSearchArea", false),
                        searchAreaX = obj.optInt("searchAreaX", 0),
                        searchAreaY = obj.optInt("searchAreaY", 0),
                        searchAreaW = obj.optInt("searchAreaW", 0),
                        searchAreaH = obj.optInt("searchAreaH", 0)
                    )
                    list.add(config)
                }
            }
            cache[name] = list
            logDiagnostic("SCRIPT", "Сценарий '$name' загружен из JSON (${list.size} шагов).")
            list
        } catch (e: Exception) {
            logError("SCRIPT", "Ошибка загрузки сценария '$name'", e)
            emptyList()
        }
    }
}
