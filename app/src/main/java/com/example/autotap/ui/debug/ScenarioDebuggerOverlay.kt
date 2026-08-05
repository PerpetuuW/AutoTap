package com.example.autotap.ui.debug

import android.content.Context
import com.example.autotap.*

class ScenarioDebuggerOverlay(private val context: Context) {
    fun update(action: AutoTapAction) {
        when (action.type) {
            ActionType.CLICK -> logAppEvent("DebugClick")
            else -> logAppEvent("DebugOther")
        }
    }
}
