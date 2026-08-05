package com.example.autotap.engine

import com.example.autotap.*

import com.example.autotap.ActionConfig
import com.example.autotap.MyAutoClickService

class ScenarioRunner(private val service: MyAutoClickService) {
    @Volatile var isRunning: Boolean = false
        private set

    var currentStepIndex: Int = 0
        private set

    fun start() {
        isRunning = true
        currentStepIndex = 0
        service.scriptExecutor.startExecutionLoop()
    }

    fun pause() {
        isRunning = false
        service.scriptExecutor.stopExecutionLoop()
    }

    fun stop() {
        isRunning = false
        currentStepIndex = 0
        service.scriptExecutor.stopExecutionLoop()
    }

    fun nextStep(totalSteps: Int) {
        if (totalSteps > 0) {
            currentStepIndex = (currentStepIndex + 1) % totalSteps
        }
    }
}
