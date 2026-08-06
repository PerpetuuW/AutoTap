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
                id = "step_1",
                title = "Шаг 1 из 8: Обзор Панели",
                message = "Добро пожаловать в AutoTap v37! Это главная панель управления. Нажмите 'Далее'.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_2",
                title = "Шаг 2 из 8: Сворачивание Панели",
                message = "Нажмите на стрелку разворота, чтобы скрыть панель в 1 строку или в плавающий шарик.",
                highlightArea = Rect(100, 200, 500, 600)
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_3",
                title = "Шаг 3 из 8: Вырезание ИИ-Масок",
                message = "Кнопка '+ ДЕЙСТВИЕ' открывает прицел. Рамка вырезает реальные пиксели с экрана.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_4",
                title = "Шаг 4 из 8: Мультипоиск",
                message = "ИИ ищет несколько масок одновременно и запрашивает свежий снимок экрана на каждом шаге.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_5",
                title = "Шаг 5 из 8: Запись Джойстика",
                message = "В режиме записи движение Knob управляет игрой 25 FPS и логирует путь в сценарий.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_6",
                title = "Шаг 6 из 8: Защита от Само-кликов",
                message = "Во время жестов оверлеи невидимы для кликов благодаря флагам NOT_TOUCHABLE.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_7",
                title = "Шаг 7 из 8: Просмотр Логов",
                message = "Все события пишутся в error_log.txt с миллисекундами и ротацией 512 КБ.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_8",
                title = "Шаг 8 из 8: Готово!",
                message = "Поздравляем! Обучение завершено. Нажмите 'Завершить'.",
                autoAdvance = false
            )
        )

        currentStepIndex = 0
        isTutorialActive = true
        logDiagnostic("TUTORIAL", "Запущен полный курс обучения (${steps.size} шагов).")
        showCurrentStep()
    }

    fun nextStep() {
        if (!isTutorialActive) return
        currentStepIndex++
        if (currentStepIndex >= steps.size) {
            logDiagnostic("TUTORIAL", "Обучение полностью завершено.")
            stopTutorial()
            return
        }
        showCurrentStep()
    }

    fun previousStep() {
        if (!isTutorialActive) return
        if (currentStepIndex > 0) {
            currentStepIndex--
            logDiagnostic("TUTORIAL", "Возврат на шаг $currentStepIndex")
            showCurrentStep()
        }
    }

    fun stopTutorial() {
        isTutorialActive = false
        currentStepIndex = 0
        service.overlayManager.tutorialOverlay.hide()
        logDiagnostic("TUTORIAL", "Обучение остановлено.")
    }

    private fun showCurrentStep() {
        if (currentStepIndex in 0 until steps.size) {
            val step = steps[currentStepIndex]
            service.overlayManager.tutorialOverlay.show()
            service.overlayManager.tutorialOverlay.renderStep(step)
        }
    }
}
