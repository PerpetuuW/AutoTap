package com.example.autotap.engine

import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic

class ScenarioRunner(private val service: MyAutoClickService) {
    private val scriptExecutor = ScriptExecutor(service)

    fun startExecutionLoop() {
        logDiagnostic("SCRIPT", "ScenarioRunner: Запуск цикла исполнения сценария.")
        scriptExecutor.start()
    }

    fun stopExecutionLoop() {
        logDiagnostic("SCRIPT", "ScenarioRunner: Остановка цикла исполнения сценария.")
        scriptExecutor.stop()
    }
}
