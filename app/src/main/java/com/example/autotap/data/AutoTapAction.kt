package com.example.autotap.data

import android.graphics.Rect
import android.graphics.RectF
import org.json.JSONObject
import com.example.autotap.*

enum class ActionType {
    CLICK, SWIPE, AI_COLOR_SCAN, DELAY
}

data class AutoTapAction(
    val id: String = java.util.UUID.randomUUID().toString(),
    var index: Int = 1,
    var type: ActionType = ActionType.CLICK,
    var x: Int = 0,
    var y: Int = 0,
    var endX: Int = 0,
    var endY: Int = 0,
    var durationMs: Long = 100L,
    var delayAfterMs: Long = 500L,
    var targetColorHex: String = "#FF0000",
    var colorTolerance: Int = 15,
    var searchRegion: Rect = Rect(0, 0, 0, 0)
) {
    fun toRectF(): RectF = RectF(
        searchRegion.left.toFloat(),
        searchRegion.top.toFloat(),
        searchRegion.right.toFloat(),
        searchRegion.bottom.toFloat()
    )

    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("id", id)
        json.put("index", index)
        json.put("type", type.name)
        json.put("x", x)
        json.put("y", y)
        json.put("endX", endX)
        json.put("endY", endY)
        json.put("durationMs", durationMs)
        json.put("delayAfterMs", delayAfterMs)
        json.put("targetColorHex", targetColorHex)
        json.put("colorTolerance", colorTolerance)
        json.put("left", searchRegion.left)
        json.put("top", searchRegion.top)
        json.put("right", searchRegion.right)
        json.put("bottom", searchRegion.bottom)
        return json
    }

    companion object {
        fun fromRectF(rectF: RectF, type: ActionType = ActionType.CLICK): AutoTapAction {
            return AutoTapAction(
                type = type,
                searchRegion = Rect(rectF.left.toInt(), rectF.top.toInt(), rectF.right.toInt(), rectF.bottom.toInt())
            )
        }

        fun fromJson(jsonStr: String): AutoTapAction {
            return fromJson(JSONObject(jsonStr))
        }

        fun fromJson(json: JSONObject): AutoTapAction {
            return AutoTapAction(
                id = json.optString("id", java.util.UUID.randomUUID().toString()),
                index = json.optInt("index", 1),
                type = ActionType.valueOf(json.optString("type", ActionType.CLICK.name)),
                x = (json.opt("x") as? Number)?.toInt() ?: 0,
                y = (json.opt("y") as? Number)?.toInt() ?: 0,
                endX = (json.opt("endX") as? Number)?.toInt() ?: 0,
                endY = (json.opt("endY") as? Number)?.toInt() ?: 0,
                durationMs = (json.opt("durationMs") as? Number)?.toLong() ?: 100L,
                delayAfterMs = (json.opt("delayAfterMs") as? Number)?.toLong() ?: 500L,
                targetColorHex = json.optString("targetColorHex", "#FF0000"),
                colorTolerance = (json.opt("colorTolerance") as? Number)?.toInt() ?: 15,
                searchRegion = Rect(
                    (json.opt("left") as? Number)?.toInt() ?: 0,
                    (json.opt("top") as? Number)?.toInt() ?: 0,
                    (json.opt("right") as? Number)?.toInt() ?: 0,
                    (json.opt("bottom") as? Number)?.toInt() ?: 0
                )
            )
        }
    }
}
