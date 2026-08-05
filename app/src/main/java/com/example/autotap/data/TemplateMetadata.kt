package com.example.autotap.data

import com.example.autotap.*

import android.graphics.Rect
import org.json.JSONObject

data class TemplateMetadata(
    var width: Int = 0,
    var height: Int = 0,
    var dpi: Int = 480,
    var scale: Float = 1.0f,
    var boundingBox: Rect = Rect(0, 0, 0, 0),
    var similarityPercent: Int = 70,
    var isCircleShape: Boolean = true,
    var version: Int = 1,
    var timestamp: Long = System.currentTimeMillis()
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("width", width)
        put("height", height)
        put("dpi", dpi)
        put("scale", scale.toDouble())
        put("originX", boundingBox.left)
        put("originY", boundingBox.top)
        put("originW", boundingBox.width())
        put("originH", boundingBox.height())
        put("similarityPercent", similarityPercent)
        put("isCircleShape", isCircleShape)
        put("version", version)
        put("timestamp", timestamp)
    }

    companion object {
        fun fromJson(obj: JSONObject): TemplateMetadata {
            val x = obj.optInt("originX", 0)
            val y = obj.optInt("originY", 0)
            val w = obj.optInt("originW", 0)
            val h = obj.optInt("originH", 0)
            return TemplateMetadata(
                width = obj.optInt("width", w),
                height = obj.optInt("height", h),
                dpi = obj.optInt("dpi", 480),
                scale = obj.optDouble("scale", 1.0).toFloat(),
                boundingBox = Rect(x, y, x + w, y + h),
                similarityPercent = obj.optInt("similarityPercent", 70),
                isCircleShape = obj.optBoolean("isCircleShape", true),
                version = obj.optInt("version", 1),
                timestamp = obj.optLong("timestamp", System.currentTimeMillis())
            )
        }
    }
}
