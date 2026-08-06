package com.example.autotap.engine

import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType

class ActionEditorEngine {

    fun updateSimilarity(action: ActionConfig, newPercent: Int): ActionConfig {
        action.similarityPercent = newPercent.coerceIn(10, 100)
        return action
    }

    fun setActionType(action: ActionConfig, newType: ActionType): ActionConfig {
        action.type = newType
        return action
    }
}
