package com.example.autotap.engine

import com.example.autotap.*

import android.graphics.Bitmap
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.TemplateMatcher
import org.json.JSONObject
import kotlin.math.abs

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

        // Фильтрация стабильности: кандидат должен быть зафиксирован >= 2 раз в одной пространственной зоне (15px)
        val stableCandidates = ArrayList<MatchCandidate>()
        for (c1 in candidates) {
            var matchCount = 0
            for (c2 in candidates) {
                if (abs(c1.rect.left - c2.rect.left) <= 15 && abs(c1.rect.top - c2.rect.top) <= 15) {
                    matchCount++
                }
            }
            if (matchCount >= 2 || candidates.size < 2) {
                stableCandidates.add(c1)
            }
        }

        val targetList = if (stableCandidates.isNotEmpty()) stableCandidates else candidates
        return targetList.maxByOrNull { it.score }
    }
}
