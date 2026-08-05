package com.example.autotap.engine

import android.graphics.Bitmap
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.TemplateMatcher
import org.json.JSONObject

object MultiFrameMatcher {
    fun matchMultiFrame(
        frames: List<Bitmap>,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): MatchCandidate? {
        if (frames.isEmpty()) return null
        val candidates = ArrayList<MatchCandidate>()
        for (frame in frames) {
            val match = TemplateMatcher.findTemplateCandidatesCoarseFine(frame, template, meta, config).firstOrNull()
            if (match != null) candidates.add(match)
        }
        if (candidates.isEmpty()) return null
        return candidates.maxByOrNull { it.score }
    }
}
