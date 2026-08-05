package com.example.autotap

import android.graphics.PointF
import android.graphics.Rect
import android.view.View
import com.example.autotap.data.TemplateMetadata
import org.json.JSONArray
import org.json.JSONObject

data class ActionConfig(
    var id: Int = 0,
    var type: ActionType = ActionType.CLICK,

    var xNorm: Float = 0f,
    var yNorm: Float = 0f,
    var endXNorm: Float = 0f,
    var endYNorm: Float = 0f,

    var delay: Long = 500L,
    var repeatCount: Int = 1,
    var randomRadius: Int = 0,
    var holdDuration: Long = 1000L,

    var waitType: String = "TIME",
    var loopType: String = "COUNT",
    var loopStartIndex: Int = 0,
    var loopCount: Int = 1,

    var selectedTemplateIndex: Int = -1,
    var multiTemplateIndices: ArrayList<Int> = ArrayList(),
    var clickAiTarget: Boolean = true,
    var targetScriptToLoad: String = "",
    var jumpToStepOnMatch: Int = -1,

    var aiTimeoutSeconds: Int = 15,
    var similarityPercent: Int = 70,
    var scanIntervalSeconds: Int = 5,
    var postMatchDelaySeconds: Int = 3,
    var playAudioOnMatch: Boolean = false,

    var isFastMode: Boolean = true,
    var exactMatchOnly: Boolean = false,
    var bestMatchAuto: Boolean = true,
    var semiTransparentMode: Boolean = false,
    var showSearchVisualizer: Boolean = true,
    var shapeOnlyMode: Boolean = false,
    var hybridCascadeMode: Boolean = true,
    var multiScaleSearch: Boolean = false,
    var autoTuningMode: Boolean = false,

    var customSearchArea: Boolean = false,
    var searchAreaXNorm: Float = 0f,
    var searchAreaYNorm: Float = 0f,
    var searchAreaWNorm: Float = 1f,
    var searchAreaHNorm: Float = 1f,

    var joystickPath: ArrayList<PointF> = ArrayList(),
    var calibratedRectNorm: Rect? = null,
    var templateMetadata: TemplateMetadata? = null,

    var dpi: Int = 480,
    var scaleFactor: Float = 1.0f,
    var version: Int = 35,
    var createdAt: Long = System.currentTimeMillis(),
    var updatedAt: Long = System.currentTimeMillis(),

    @Transient var startView: View? = null,
    @Transient var endView: View? = null
) {
    companion object {
        fun fromJson(obj: JSONObject): ActionConfig {
            val cfg = ActionConfig()

            cfg.id = obj.optInt("id", 0)
            cfg.type = ActionType.valueOf(obj.optString("type", "CLICK"))

            cfg.xNorm = obj.optDouble("xNorm", 0.0).toFloat()
            cfg.yNorm = obj.optDouble("yNorm", 0.0).toFloat()
            cfg.endXNorm = obj.optDouble("endXNorm", 0.0).toFloat()
            cfg.endYNorm = obj.optDouble("endYNorm", 0.0).toFloat()

            cfg.delay = obj.optLong("delay", 500L)
            cfg.repeatCount = obj.optInt("repeatCount", 1)
            cfg.randomRadius = obj.optInt("randomRadius", 0)
            cfg.holdDuration = obj.optLong("holdDuration", 1000L)

            cfg.waitType = obj.optString("waitType", "TIME")
            cfg.loopType = obj.optString("loopType", "COUNT")
            cfg.loopStartIndex = obj.optInt("loopStartIndex", 0)
            cfg.loopCount = obj.optInt("loopCount", 1)

            cfg.selectedTemplateIndex = obj.optInt("selectedTemplateIndex", -1)

            val arrMulti = obj.optJSONArray("multiTemplateIndices") ?: JSONArray()
            cfg.multiTemplateIndices = ArrayList<Int>().apply {
                for (i in 0 until arrMulti.length()) add(arrMulti.optInt(i))
            }

            cfg.clickAiTarget = obj.optBoolean("clickAiTarget", true)
            cfg.targetScriptToLoad = obj.optString("targetScriptToLoad", "")
            cfg.jumpToStepOnMatch = obj.optInt("jumpToStepOnMatch", -1)

            cfg.aiTimeoutSeconds = obj.optInt("aiTimeoutSeconds", 15)
            cfg.similarityPercent = obj.optInt("similarityPercent", 70)
            cfg.scanIntervalSeconds = obj.optInt("scanIntervalSeconds", 5)
            cfg.postMatchDelaySeconds = obj.optInt("postMatchDelaySeconds", 3)
            cfg.playAudioOnMatch = obj.optBoolean("playAudioOnMatch", false)

            cfg.isFastMode = obj.optBoolean("isFastMode", true)
            cfg.exactMatchOnly = obj.optBoolean("exactMatchOnly", false)
            cfg.bestMatchAuto = obj.optBoolean("bestMatchAuto", true)
            cfg.semiTransparentMode = obj.optBoolean("semiTransparentMode", false)
            cfg.showSearchVisualizer = obj.optBoolean("showSearchVisualizer", true)
            cfg.shapeOnlyMode = obj.optBoolean("shapeOnlyMode", false)
            cfg.hybridCascadeMode = obj.optBoolean("hybridCascadeMode", true)
            cfg.multiScaleSearch = obj.optBoolean("multiScaleSearch", false)
            cfg.autoTuningMode = obj.optBoolean("autoTuningMode", false)

            cfg.customSearchArea = obj.optBoolean("customSearchArea", false)
            cfg.searchAreaXNorm = obj.optDouble("searchAreaXNorm", 0.0).toFloat()
            cfg.searchAreaYNorm = obj.optDouble("searchAreaYNorm", 0.0).toFloat()
            cfg.searchAreaWNorm = obj.optDouble("searchAreaWNorm", 1.0).toFloat()
            cfg.searchAreaHNorm = obj.optDouble("searchAreaHNorm", 1.0).toFloat()

            cfg.dpi = obj.optInt("dpi", 480)
            cfg.scaleFactor = obj.optDouble("scaleFactor", 1.0).toFloat()
            cfg.version = obj.optInt("version", 35)
            cfg.createdAt = obj.optLong("createdAt", System.currentTimeMillis())
            cfg.updatedAt = obj.optLong("updatedAt", System.currentTimeMillis())

            if (obj.has("templateMetadata")) {
                cfg.templateMetadata = TemplateMetadata.fromJson(obj.getJSONObject("templateMetadata"))
            }

            val arrPath = obj.optJSONArray("joystickPath") ?: JSONArray()
            cfg.joystickPath = ArrayList<PointF>().apply {
                for (i in 0 until arrPath.length()) {
                    val p = arrPath.optJSONObject(i)
                    add(PointF(p.optDouble("x", 0.0).toFloat(), p.optDouble("y", 0.0).toFloat()))
                }
            }

            return cfg
        }
    }

    fun toJson(): JSONObject {
        val obj = JSONObject()
        obj.put("id", id)
        obj.put("type", type.name)
        obj.put("xNorm", xNorm)
        obj.put("yNorm", yNorm)
        obj.put("endXNorm", endXNorm)
        obj.put("endYNorm", endYNorm)
        obj.put("delay", delay)
        obj.put("repeatCount", repeatCount)
        obj.put("randomRadius", randomRadius)
        obj.put("holdDuration", holdDuration)
        obj.put("waitType", waitType)
        obj.put("loopType", loopType)
        obj.put("loopStartIndex", loopStartIndex)
        obj.put("loopCount", loopCount)
        obj.put("selectedTemplateIndex", selectedTemplateIndex)
        obj.put("multiTemplateIndices", JSONArray(multiTemplateIndices))
        obj.put("clickAiTarget", clickAiTarget)
        obj.put("targetScriptToLoad", targetScriptToLoad)
        obj.put("jumpToStepOnMatch", jumpToStepOnMatch)
        obj.put("aiTimeoutSeconds", aiTimeoutSeconds)
        obj.put("similarityPercent", similarityPercent)
        obj.put("scanIntervalSeconds", scanIntervalSeconds)
        obj.put("postMatchDelaySeconds", postMatchDelaySeconds)
        obj.put("playAudioOnMatch", playAudioOnMatch)
        obj.put("isFastMode", isFastMode)
        obj.put("exactMatchOnly", exactMatchOnly)
        obj.put("bestMatchAuto", bestMatchAuto)
        obj.put("semiTransparentMode", semiTransparentMode)
        obj.put("showSearchVisualizer", showSearchVisualizer)
        obj.put("shapeOnlyMode", shapeOnlyMode)
        obj.put("hybridCascadeMode", hybridCascadeMode)
        obj.put("multiScaleSearch", multiScaleSearch)
        obj.put("autoTuningMode", autoTuningMode)
        obj.put("customSearchArea", customSearchArea)
        obj.put("searchAreaXNorm", searchAreaXNorm)
        obj.put("searchAreaYNorm", searchAreaYNorm)
        obj.put("searchAreaWNorm", searchAreaWNorm)
        obj.put("searchAreaHNorm", searchAreaHNorm)
        obj.put("dpi", dpi)
        obj.put("scaleFactor", scaleFactor.toDouble())
        obj.put("version", version)
        obj.put("createdAt", createdAt)
        obj.put("updatedAt", System.currentTimeMillis())

        templateMetadata?.let { obj.put("templateMetadata", it.toJson()) }

        val arrPath = JSONArray()
        joystickPath.forEach { p ->
            arrPath.put(JSONObject().apply {
                put("x", p.x)
                put("y", p.y)
            })
        }
        obj.put("joystickPath", arrPath)
        return obj
    }
}
