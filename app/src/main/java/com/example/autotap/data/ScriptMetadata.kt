package com.example.autotap.data

import com.example.autotap.*

import org.json.JSONObject

data class ScriptMetadata(
    var name: String = "",
    var stepCount: Int = 0,
    var stepSummary: String = "",
    var loopCount: Int = 1,
    var isInfinite: Boolean = false,
    var relayScript: String = "",
    var createdAt: Long = System.currentTimeMillis(),
    var modifiedAt: Long = System.currentTimeMillis()
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("name", name)
        put("stepCount", stepCount)
        put("stepSummary", stepSummary)
        put("loopCount", loopCount)
        put("isInfinite", isInfinite)
        put("relayScript", relayScript)
        put("createdAt", createdAt)
        put("modifiedAt", modifiedAt)
    }

    companion object {
        fun fromJson(obj: JSONObject): ScriptMetadata {
            return ScriptMetadata(
                name = obj.optString("name", ""),
                stepCount = obj.optInt("stepCount", 0),
                stepSummary = obj.optString("stepSummary", ""),
                loopCount = obj.optInt("loopCount", 1),
                isInfinite = obj.optBoolean("isInfinite", false),
                relayScript = obj.optString("relayScript", ""),
                createdAt = obj.optLong("createdAt", System.currentTimeMillis()),
                modifiedAt = obj.optLong("modifiedAt", System.currentTimeMillis())
            )
        }
    }
}
