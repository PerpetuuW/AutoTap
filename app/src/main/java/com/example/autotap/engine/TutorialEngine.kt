package com.example.autotap.engine

import android.graphics.Rect
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStepConfig

class TutorialEngine(private val service: MyAutoClickService) {

    @Volatile var isTutorialActive = false
        private set

    private var currentStepIndex = 0
    private val steps = mutableListOf<TutorialStepConfig>()

    private fun getControlPanelChildBounds(service: MyAutoClickService, childIdName: String): Rect {
        val panel = service.overlayManager.controlPanel
        val panelView = panel.overlayView ?: return Rect(100, 200, 500, 400)
        val lp = panel.layoutParams ?: return Rect(100, 200, 500, 400)
        val child = panelView.findViewByNames(childIdName)

        return if (child != null && child.width > 0 && child.height > 0) {
            val childX = lp.x + child.left
            val childY = lp.y + child.top
            Rect(childX, childY, childX + child.width, childY + child.height)
        } else {
            val w = if (panelView.width > 0) panelView.width else 300
            val h = if (panelView.height > 0) panelView.height else 150
            Rect(lp.x, lp.y, lp.x + w, lp.y + h)
        }
    }

    fun startDefaultTutorial() {
        steps.clear()
        steps.add(
            TutorialStepConfig(
                id = "step_1",
                title = "Шаг 1 из 8: Обзор Панели",
                message = "Добро пожаловать в AutoTap PRO! Это главная панель управления. Нажмите 'Далее'.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_2",
                title = "Шаг 2 из 8: Сворачивание Панели",
                message = "Нажмите на кнопку ≡, чтобы скрыть панель в 1 строку или в плавающий шарик."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_3",
                title = "Шаг 3 из 8: Вырезание ИИ-Масок",
                message = "Кнопка 📷 откроет прицел. Рамка вырежет точные пиксели с экрана игры."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_4",
                title = "Шаг 4 из 8: Мультипоиск",
                message = "ИИ ищет шаблоны одновременно на скорости 60 FPS и нажимает на найденные цели."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_5",
                title = "Шаг 5 из 8: Запись Джойстика",
                message = "Джойстик передает плавное удержание (continueStroke) и одновременно пишет путь."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_6",
                title = "Шаг 6 из 8: Защита от Само-кликов",
                message = "Во время жестов панели невидимы для кликов благодаря Anti-Self-Click Guard."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_7",
                title = "Шаг 7 из 8: Просмотр Логов",
                message = "Все события пишутся в диалоговое окно логов с миллисекундами и поддержкой бэкапов."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_8",
                title = "Шаг 8 из 8: Готово!",
                message = "Поздравляем! Обучение завершено. Нажмите 'Завершить'."
            )
        )

        currentStepIndex = 0
        isTutorialActive = true
        logDiagnostic("TUTORIAL", "Запущен курс обучения с снайперской подсветкой кнопок.")
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
            val targetBounds = when (step.id) {
                "step_2" -> getControlPanelChildBounds(service, "btnToggleMenu")
                "step_3" -> getControlPanelChildBounds(service, "btnCapturePool")
                "step_4" -> getControlPanelChildBounds(service, "btnAdd")
                "step_5" -> getControlPanelChildBounds(service, "btnToggleJoystick")
                else -> {
                    val panel = service.overlayManager.controlPanel
                    val v = panel.overlayView
                    val lp = panel.layoutParams
                    if (v != null && lp != null) {
                        Rect(lp.x, lp.y, lp.x + v.width, lp.y + v.height)
                    } else Rect(100, 200, 500, 400)
                }
            }

            val updatedStep = step.copy(highlightArea = targetBounds)
            service.overlayManager.tutorialOverlay.show()
            service.overlayManager.tutorialOverlay.renderStep(updatedStep)
        }
    }
}
