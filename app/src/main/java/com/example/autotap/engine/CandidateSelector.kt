package com.example.autotap.engine

import com.example.autotap.MatchCandidate

object CandidateSelector {
    fun selectBest(candidates: List<MatchCandidate>): MatchCandidate? {
        return candidates.maxByOrNull { it.score }
    }
}
