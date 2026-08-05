package com.example.autotap.engine

import com.example.autotap.*

data class SearchModes(
    val exactMatchOnly: Boolean = false,
    val shapeOnlyMode: Boolean = false,
    val hybridCascadeMode: Boolean = true,
    val multiScaleSearch: Boolean = false,
    val isFastMode: Boolean = true
)
