package com.example.autotap.engine

import com.example.autotap.engine.ai.MatchCandidate

class CandidateSelector {

    fun selectBestCandidate(candidates: List<MatchCandidate>): MatchCandidate? {
        if (candidates.isEmpty()) return null
        return candidates.maxByOrNull { it.score }
    }
}
