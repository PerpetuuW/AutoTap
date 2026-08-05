package com.example.autotap

import android.content.Context
import android.graphics.Color
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

data class AutoTapAction(
    val id: String,
    val type: ActionType,
    val x: Int,
    val y: Int,
    val endX: Int = 0,
    val endY: Int = 0,
    val durationMs: Long = 100L,
    val delayAfterMs: Long = 500L,
    val targetColor: Int = Color.BLACK,
    val colorTolerance: Int = 15
) {
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
        }
    }

    companion object {
        fun fromJsonObject(json: JSONObject): AutoTapAction {
            return AutoTapAction(
                id = json.getString("id"),
                type = ActionType.valueOf(json.getString("type")),
                x = json.getInt("x"),
                y = json.getInt("y"),
                endX = json.optInt("endX", 0),
                endY = json.optInt("endY", 0),
                durationMs = json.optLong("durationMs", 100L),
                delayAfterMs = json.optLong("delayAfterMs", 500L),
                targetColor = json.optInt("targetColor", Color.BLACK),
                colorTolerance = json.optInt("colorTolerance", 15)
            )
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
                    if (bakFile.exists()) {
                        bakFile.delete()
                    }
                    if (!targetFile.renameTo(bakFile)) {
                        DiagnosticLogger.log("AtomicScriptManager", "Failed to backup target file to .bak")
                    }
                }

                if (!tmpFile.renameTo(targetFile)) {
                    DiagnosticLogger.log("AtomicScriptManager", "Failed to rename .tmp to target file")
                    if (bakFile.exists() && !targetFile.exists()) {
                        bakFile.renameTo(targetFile)
                    }
                    return false
                }

                DiagnosticLogger.log(
                    "AtomicScriptManager",
                    "Script saved successfully",
                    mapOf("file" to fileName, "durationMs" to (System.currentTimeMillis() - startTime), "count" to actions.size)
                )
                return true

            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Critical error saving script: ${e.message}")
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
            if (fileToRead == null) {
                DiagnosticLogger.log("AtomicScriptManager", "No valid script file found for: $fileName")
                return list
            }

            try {
                val content = fileToRead.readText(Charsets.UTF_8)
                val jsonArray = JSONArray(content)
                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    list.add(AutoTapAction.fromJsonObject(obj))
                }
                DiagnosticLogger.log("AtomicScriptManager", "Script loaded", mapOf("file" to fileName, "count" to list.size))
            } catch (e: Exception) {
                DiagnosticLogger.log("AtomicScriptManager", "Error parsing script JSON: ${e.message}")
            }
            return list
        }
    }
}
