package com.example.autotap.data

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
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
                    put("jumpToStepOnMatch", action.jumpToStepOnMatch ?: -1)
                    put("jumpToStepOnFail", action.jumpToStepOnFail ?: -1)
                    val multiIndicesArr = JSONArray()
                    for (idx in action.multiTemplateIndices) {
                        multiIndicesArr.put(idx)
                    }
                    put("multiTemplateIndices", multiIndicesArr)
                    put("targetScriptToLoad", action.targetScriptToLoad ?: "")
                    put("randomRadius", action.randomRadius)
                    put("scanIntervalSeconds", action.scanIntervalSeconds)
                    put("clickAiTarget", action.clickAiTarget)
                    put("loopUntilStopped", action.loopUntilStopped)
                    put("shapeOnlyMode", action.shapeOnlyMode)
                    put("autoTuningMode", action.autoTuningMode)
                    put("hybridCascadeMode", action.hybridCascadeMode)
                    put("multiScaleSearch", action.multiScaleSearch)
                    put("notificationMode", action.notificationMode)
                    put("longPressDuration", action.longPressDuration)
                    put("clickOffsetX", action.clickOffsetX)
                    put("clickOffsetY", action.clickOffsetY)

                    val joystickArr = JSONArray()
                    for (pt in action.joystickPath) {
                        val ptObj = JSONObject()
                        ptObj.put("x", pt.x)
                        ptObj.put("y", pt.y)
                        joystickArr.put(ptObj)
                    }
                    put("joystickPath", joystickArr)
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
                    val matchJump = obj.optInt("jumpToStepOnMatch", -1)
                    val failJump = obj.optInt("jumpToStepOnFail", -1)

                    val multiIndicesList = mutableListOf<Int>()
                    val multiArr = obj.optJSONArray("multiTemplateIndices")
                    if (multiArr != null) {
                        for (j in 0 until multiArr.length()) {
                            multiIndicesList.add(multiArr.getInt(j))
                        }
                    }

                    val joystickList = mutableListOf<android.graphics.PointF>()
                    val joyArr = obj.optJSONArray("joystickPath")
                    if (joyArr != null) {
                        for (j in 0 until joyArr.length()) {
                            val ptObj = joyArr.getJSONObject(j)
                            joystickList.add(android.graphics.PointF(ptObj.optDouble("x", 0.0).toFloat(), ptObj.optDouble("y", 0.0).toFloat()))
                        }
                    }

                    val config = ActionConfig(
                        type = try { ActionType.valueOf(obj.optString("type", ActionType.CLICK.name)) } catch (_: Exception) { ActionType.CLICK },
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
                        searchAreaH = obj.optInt("searchAreaH", 0),
                        jumpToStepOnMatch = if (matchJump != -1) matchJump else null,
                        jumpToStepOnFail = if (failJump != -1) failJump else null,
                        multiTemplateIndices = multiIndicesList,
                        targetScriptToLoad = obj.optString("targetScriptToLoad", "").takeIf { it.isNotEmpty() },
                        randomRadius = obj.optDouble("randomRadius", 0.0).toFloat(),
                        scanIntervalSeconds = obj.optDouble("scanIntervalSeconds", 0.1).toFloat(),
                        clickAiTarget = obj.optBoolean("clickAiTarget", false),
                        loopUntilStopped = obj.optBoolean("loopUntilStopped", true),
                        shapeOnlyMode = obj.optBoolean("shapeOnlyMode", false),
                        autoTuningMode = obj.optBoolean("autoTuningMode", true),
                        hybridCascadeMode = obj.optBoolean("hybridCascadeMode", true),
                        multiScaleSearch = obj.optBoolean("multiScaleSearch", true),
                        notificationMode = obj.optInt("notificationMode", 0),
                        longPressDuration = obj.optLong("longPressDuration", 500L),
                        clickOffsetX = obj.optInt("clickOffsetX", 0),
                        clickOffsetY = obj.optInt("clickOffsetY", 0),
                        joystickPath = joystickList
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
