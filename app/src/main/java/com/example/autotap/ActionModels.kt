package com.example.autotap

import com.example.autotap.*

import android.content.Context
import android.graphics.Color
import android.graphics.Point
import android.graphics.Rect
import android.graphics.RectF
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CopyOnWriteArrayList

enum class ActionType {
    CLICK,
    SWIPE,
    COLOR_CHECK,
    LONG_PRESS,
    HOLD,
    SWIPE_PATH,
    TRIGGER,
    WAIT,
    LOOP
}

typealias ActionConfig = AutoTapAction

data class AutoTapAction(
    var id: String = "act_" + System.currentTimeMillis(),
    var type: ActionType = ActionType.CLICK,
    var x: Int = 0,
    var y: Int = 0,
    var endX: Int = 0,
    var endY: Int = 0,
    var durationMs: Long = 100L,
    var delayAfterMs: Long = 500L,
    var targetColor: Int = Color.BLACK,
    var colorTolerance: Int = 15,

    // Редактируемые var-поля с поддержкой приведения Float/Int типов
    var delay: Long = 500L,
    var repeatCount: Int = 1,
    var similarityPercent: Float = 0.8f,
    var aiTimeoutSeconds: Int = 10,
    var scanIntervalSeconds: Float = 0.5f,
    var postMatchDelaySeconds: Float = 0.0f,
    var xNorm: Float = 0f,
    var yNorm: Float = 0f,
    var endXNorm: Float = 0f,
    var endYNorm: Float = 0f,
    var selectedTemplateIndex: Int = 0,
    var dpi: Int = 160,
    var exactMatchOnly: Boolean = false,
    var shapeOnlyMode: Boolean = false,
    var hybridCascadeMode: Boolean = false,
    var multiScaleSearch: Boolean = false,
    var isFastMode: Boolean = false,
    var customSearchArea: Boolean = false,
    var searchAreaXNorm: Float = 0f,
    var searchAreaYNorm: Float = 0f,
    var searchAreaWNorm: Float = 1f,
    var searchAreaHNorm: Float = 1f,
    var calibratedRectNorm: RectF? = RectF(0f, 0f, 1f, 1f),
    var playAudioOnMatch: Boolean = false,
    var clickAiTarget: Boolean = true,
    var jumpToStepOnMatch: Int = -1,
    var jumpToStep: Int = -1,
    var targetScriptToLoad: String = "",
    var targetScript: String = "",
    var loopType: String = "COUNT",
    var multiTemplateIndices: List<Int> = emptyList(),
    var updatedAt: Long = System.currentTimeMillis(),

    var randomOffset: Int = 0,
    var randomRadius: Int = 0,
    var holdDuration: Long = 100L,
    var waitType: String = "FIXED",
    var loopCount: Int = 1,
    var loopStartIndex: Int = 0,
    var joystickPath: List<Point> = emptyList()
) {
    fun setCalibratedRect(rect: Rect) {
        calibratedRectNorm = RectF(rect.left.toFloat(), rect.top.toFloat(), rect.right.toFloat(), rect.bottom.toFloat())
    }

    fun toJsonObject(): JSONObject {
        return JSONObject().apply {
            put("id", id)
            put("type", type.name)
            put("x", x)
            put("y", y)
            put("endX", endX)
            put("endY", endY)
            put("durationMs", durationMs)
            put("delayAfterMs", delayAfterMs)
            put("targetColor", targetColor)
            put("colorTolerance", colorTolerance)
            put("delay", delay)
            put("repeatCount", repeatCount)
            put("similarityPercent", similarityPercent.toDouble())
            put("aiTimeoutSeconds", aiTimeoutSeconds)
            put("scanIntervalSeconds", scanIntervalSeconds.toDouble())
            put("postMatchDelaySeconds", postMatchDelaySeconds.toDouble())
            put("xNorm", xNorm.toDouble())
            put("yNorm", yNorm.toDouble())
            put("endXNorm", endXNorm.toDouble())
            put("endYNorm", endYNorm.toDouble())
            put("selectedTemplateIndex", selectedTemplateIndex)
            put("dpi", dpi)
            put("exactMatchOnly", exactMatchOnly)
            put("shapeOnlyMode", shapeOnlyMode)
            put("hybridCascadeMode", hybridCascadeMode)
            put("multiScaleSearch", multiScaleSearch)
            put("isFastMode", isFastMode)
            put("customSearchArea", customSearchArea)
            put("searchAreaXNorm", searchAreaXNorm.toDouble())
            put("searchAreaYNorm", searchAreaYNorm.toDouble())
            put("searchAreaWNorm", searchAreaWNorm.toDouble())
            put("searchAreaHNorm", searchAreaHNorm.toDouble())
            put("playAudioOnMatch", playAudioOnMatch)
            put("clickAiTarget", clickAiTarget)
            put("jumpToStepOnMatch", jumpToStepOnMatch)
            put("jumpToStep", jumpToStep)
            put("targetScriptToLoad", targetScriptToLoad)
            put("targetScript", targetScript)
            put("loopType", loopType)
            put("updatedAt", updatedAt)
            put("randomOffset", randomOffset)
            put("randomRadius", randomRadius)
            put("holdDuration", holdDuration)
            put("waitType", waitType)
            put("loopCount", loopCount)
            put("loopStartIndex", loopStartIndex)
        }
    }

    fun toJson(): String = toJsonObject().toString()

    companion object {
        fun fromJsonObject(json: JSONObject): AutoTapAction {
            return AutoTapAction(
                id = json.optString("id", "act_" + System.currentTimeMillis()),
                type = try { ActionType.valueOf(json.optString("type", ActionType.CLICK.name)) } catch (e: Exception) { ActionType.CLICK },
                x = json.optInt("x", 0),
                y = json.optInt("y", 0),
                endX = json.optInt("endX", 0),
                endY = json.optInt("endY", 0),
                durationMs = json.optLong("durationMs", 100L),
                delayAfterMs = json.optLong("delayAfterMs", 500L),
                targetColor = json.optInt("targetColor", Color.BLACK),
                colorTolerance = json.optInt("colorTolerance", 15),
                delay = json.optLong("delay", 500L),
                repeatCount = json.optInt("repeatCount", 1),
                similarityPercent = json.optDouble("similarityPercent", 0.8).toFloat(),
                aiTimeoutSeconds = json.optInt("aiTimeoutSeconds", 10),
                scanIntervalSeconds = json.optDouble("scanIntervalSeconds", 0.5).toFloat(),
                postMatchDelaySeconds = json.optDouble("postMatchDelaySeconds", 0.0).toFloat(),
                xNorm = json.optDouble("xNorm", 0.0).toFloat(),
                yNorm = json.optDouble("yNorm", 0.0).toFloat(),
                endXNorm = json.optDouble("endXNorm", 0.0).toFloat(),
                endYNorm = json.optDouble("endYNorm", 0.0).toFloat(),
                selectedTemplateIndex = json.optInt("selectedTemplateIndex", 0),
                dpi = json.optInt("dpi", 160),
                exactMatchOnly = json.optBoolean("exactMatchOnly", false),
                shapeOnlyMode = json.optBoolean("shapeOnlyMode", false),
                hybridCascadeMode = json.optBoolean("hybridCascadeMode", false),
                multiScaleSearch = json.optBoolean("multiScaleSearch", false),
                isFastMode = json.optBoolean("isFastMode", false),
                customSearchArea = json.optBoolean("customSearchArea", false),
                searchAreaXNorm = json.optDouble("searchAreaXNorm", 0.0).toFloat(),
                searchAreaYNorm = json.optDouble("searchAreaYNorm", 0.0).toFloat(),
                searchAreaWNorm = json.optDouble("searchAreaWNorm", 1.0).toFloat(),
                searchAreaHNorm = json.optDouble("searchAreaHNorm", 1.0).toFloat(),
                playAudioOnMatch = json.optBoolean("playAudioOnMatch", false),
                clickAiTarget = json.optBoolean("clickAiTarget", true),
                jumpToStepOnMatch = json.optInt("jumpToStepOnMatch", -1),
                jumpToStep = json.optInt("jumpToStep", -1),
                targetScriptToLoad = json.optString("targetScriptToLoad", ""),
                targetScript = json.optString("targetScript", ""),
                loopType = json.optString("loopType", "COUNT"),
                updatedAt = json.optLong("updatedAt", System.currentTimeMillis()),
                randomOffset = json.optInt("randomOffset", 0),
                randomRadius = json.optInt("randomRadius", 0),
                holdDuration = json.optLong("holdDuration", 100L),
                waitType = json.optString("waitType", "FIXED"),
                loopCount = json.optInt("loopCount", 1),
                loopStartIndex = json.optInt("loopStartIndex", 0)
            )
        }

        fun fromJson(jsonObj: JSONObject): AutoTapAction = fromJsonObject(jsonObj)

        fun fromJson(jsonStr: String): AutoTapAction {
            return try {
                fromJsonObject(JSONObject(jsonStr))
            } catch (e: Exception) {
                AutoTapAction()
            }
        }
    }
}

object DiagnosticLogger {
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US)

    fun log(tag: String, message: String, metrics: Map<String, Any> = emptyMap()) {
        val timestamp = dateFormat.format(Date())
        val metricsString = if (metrics.isNotEmpty()) {
            " | Metrics: " + metrics.entries.joinToString(", ") { "${it.key}=${it.value}" }
        } else {
            ""
        }
        val formattedMessage = "[$timestamp] [$tag] $message$metricsString"
        android.util.Log.d("AutoTap_Audit", formattedMessage)
    }
}

class AtomicScriptManager(private val context: Context) {
    private val lock = Any()

    fun saveScript(fileName: String, actions: CopyOnWriteArrayList<AutoTapAction>): Boolean {
        synchronized(lock) {
            val startTime = System.currentTimeMillis()
            val targetFile = File(context.filesDir, "$fileName.json")
            val tmpFile = File(context.filesDir, "$fileName.tmp")
            val bakFile = File(context.filesDir, "$fileName.json.bak")

            try {
                val jsonArray = JSONArray()
                for (action in actions) {
                    jsonArray.put(action.toJsonObject())
                }
                val jsonString = jsonArray.toString(2)

                FileOutputStream(tmpFile).use { fos ->
                    fos.write(jsonString.toByteArray(Charsets.UTF_8))
                    fos.flush()
                    fos.fd.sync()
                }

                JSONArray(tmpFile.readText(Charsets.UTF_8))

                if (targetFile.exists()) {
                    if (bakFile.exists()) bakFile.delete()
                    targetFile.renameTo(bakFile)
                }

                if (!tmpFile.renameTo(targetFile)) {
                    if (bakFile.exists() && !targetFile.exists()) bakFile.renameTo(targetFile)
                    return false
                }

                DiagnosticLogger.log(
                    "AtomicScriptManager",
                    "Script saved",
                    mapOf("file" to fileName, "durationMs" to (System.currentTimeMillis() - startTime), "count" to actions.size)
                )
                return true
            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Error saving script: ${e.message}")
                if (tmpFile.exists()) tmpFile.delete()
                return false
            }
        }
    }

    fun loadScript(fileName: String): CopyOnWriteArrayList<AutoTapAction> {
        synchronized(lock) {
            val targetFile = File(context.filesDir, "$fileName.json")
            val bakFile = File(context.filesDir, "$fileName.json.bak")
            val fileToRead = when {
                targetFile.exists() && targetFile.length() > 0 -> targetFile
                bakFile.exists() && bakFile.length() > 0 -> bakFile
                else -> null
            }

            val list = CopyOnWriteArrayList<AutoTapAction>()
            if (fileToRead == null) return list

            try {
                val jsonArray = JSONArray(fileToRead.readText(Charsets.UTF_8))
                for (i in 0 until jsonArray.length()) {
                    list.add(AutoTapAction.fromJsonObject(jsonArray.getJSONObject(i)))
                }
            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Error loading script: ${e.message}")
            }
            return list
        }
    }
}
