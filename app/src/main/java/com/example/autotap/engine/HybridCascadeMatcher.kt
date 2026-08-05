package com.example.autotap.engine

import android.graphics.Bitmap
import com.example.autotap.ActionConfig
import com.example.autotap.MatchCandidate
import com.example.autotap.TemplateMatcher
import org.json.JSONObject

object HybridCascadeMatcher {
    fun cascadeSearch(
        screen: Bitmap,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): List<MatchCandidate> {
        val candidates = TemplateMatcher.findTemplateCandidatesCoarseFine(screen, template, meta, config)
        return candidates.take(3)
    }
}
