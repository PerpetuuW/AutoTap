package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.PointF
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.engine.ai.TemplateMatcher
import com.example.autotap.model.ActionConfig

class MultiFrameMatcher(private val templateMatcher: TemplateMatcher) {

    fun matchFrames(
        frames: List<Bitmap>,
        action: ActionConfig
    ): List<MatchCandidate> {
        val allCandidates = mutableListOf<MatchCandidate>()
        for (frame in frames) {
            val candidates = templateMatcher.matchSingleTemplate(frame, action)
            allCandidates.addAll(candidates)
        }
        return templateMatcher.rankCandidates(allCandidates)
    }

    fun computeStablePoint(candidates: List<MatchCandidate>): PointF? {
        if (candidates.isEmpty()) return null
        val bestCandidate = candidates.maxByOrNull { it.score }
        return bestCandidate?.point
    }
}
