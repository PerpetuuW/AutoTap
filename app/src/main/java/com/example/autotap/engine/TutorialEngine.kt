package com.example.autotap.engine

import android.graphics.Rect
import com.example.autotap.MyAutoClickService
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStepConfig

class TutorialEngine(private val service: MyAutoClickService) {

    @Volatile var isTutorialActive = false
        private set

    private var currentStepIndex = 0
    private val steps = mutableListOf<TutorialStepConfig>()

    fun startDefaultTutorial() {
        steps.clear()
        steps.add(
            TutorialStepConfig(
                id = "step_1_welcome",
                message = "Добро пожаловать в AutoTap v35! Нажмите 'Далее' для начала обзора.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_2_panel",
                message = "Это Панель Управления. Нажмите '+ ДЕЙСТВИЕ', чтобы добавить новый шаг.",
                highlightArea = Rect(100, 200, 500, 600),
                waitForClickOnArea = Rect(100, 200, 500, 600)
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_3_finish",
                message = "Отлично! Теперь вы готовы создавать авто-сценарии. Нажмите 'Завершить'.",
                autoAdvance = false
            )
        )

        currentStepIndex = 0
        isTutorialActive = true
        logDiagnostic("TUTORIAL", "Запущен интерактивный туториал (${steps.size} шагов).")
        showCurrentStep()
    }

    fun nextStep() {
        if (!isTutorialActive) return
        currentStepIndex++
        if (currentStepIndex >= steps.size) {
            logDiagnostic("TUTORIAL", "Интерактивный туториал полностью завершен.")
            stopTutorial()
            return
        }
        showCurrentStep()
    }

    fun stopTutorial() {
        isTutorialActive = false
        currentStepIndex = 0
        service.overlayManager.tutorialOverlay.hide()
        logDiagnostic("TUTORIAL", "Туториал остановлен.")
    }

    private fun showCurrentStep() {
        if (currentStepIndex in 0 until steps.size) {
            val step = steps[currentStepIndex]
            service.overlayManager.tutorialOverlay.show()
            service.overlayManager.tutorialOverlay.renderStep(step)
        }
    }
}
