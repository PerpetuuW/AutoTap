package com.example.autotap.engine

import android.graphics.Rect
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.dpToPx
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.TutorialStepConfig

class TutorialEngine(private val service: MyAutoClickService) {

    @Volatile var isTutorialActive = false
        private set

    private var currentStepIndex = 0
    private val steps = mutableListOf<TutorialStepConfig>()

    private fun getControlPanelChildBounds(
        service: MyAutoClickService,
        childIdName: String,
        callback: (Rect) -> Unit
    ) {
        val panel = service.overlayManager.controlPanel
        val panelView = panel.overlayView

        if (panelView == null) {
            callback(Rect(100, 200, 500, 400))
            return
        }

        val mainRow = panelView.findViewByNames("layoutMainRow")
        val subMenu = panelView.findViewByNames("layoutSubMenu")

        if (mainRow != null) mainRow.visibility = View.VISIBLE
        if (subMenu != null) subMenu.visibility = View.VISIBLE

        panelView.measure(
            View.MeasureSpec.makeMeasureSpec(service.resources.displayMetrics.widthPixels, View.MeasureSpec.AT_MOST),
            View.MeasureSpec.makeMeasureSpec(service.resources.displayMetrics.heightPixels, View.MeasureSpec.AT_MOST)
        )

        panelView.post {
            val child = panelView.findViewByNames(childIdName)
            val paddingPx = 6.dpToPx(service)

            if (child != null && child.width > 0 && child.height > 0) {
                val location = IntArray(2)
                child.getLocationOnScreen(location)
                val rect = Rect(
                    location[0] - paddingPx,
                    location[1] - paddingPx,
                    location[0] + child.width + paddingPx,
                    location[1] + child.height + paddingPx
                )
                callback(rect)
            } else {
                val location = IntArray(2)
                panelView.getLocationOnScreen(location)
                val w = if (panelView.width > 0) panelView.width else 300
                val h = if (panelView.height > 0) panelView.height else 150
                callback(Rect(location[0], location[1], location[0] + w, location[1] + h))
            }
        }
    }

    fun startDefaultTutorial() {
        steps.clear()
        
        // Последовательный порядок по кнопкам панели
        steps.add(
            TutorialStepConfig(
                id = "step_1",
                title = "Шаг 1 из 9: Обзор Панели",
                message = "Добро пожаловать в AutoTap PRO! Это главная панель управления. Нажмите 'Далее'.",
                autoAdvance = false
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_2",
                title = "Шаг 2 из 9: Кнопка СТАРТ",
                message = "Кнопка ► запускает и останавливает выполнение шагов кликера."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_3",
                title = "Шаг 3 из 9: Добавление Шагов",
                message = "Кнопка + добавляет клики, свайпы и шаги ИИ-поиска."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_4",
                title = "Шаг 4 из 9: Вырезание ИИ-Масок",
                message = "Кнопка 📷 откроет прицел. Рамка вырежет точные картинки с экрана игры."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_5",
                title = "Шаг 5 из 9: Справка ?",
                message = "Кнопка ? вызовет это обучение и подробную справку в любой момент."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_6",
                title = "Шаг 6 из 9: Сворачивание Меню ≡",
                message = "Кнопка ≡ скрывает панель в 1 строку или открывает нижнее меню."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_7",
                title = "Шаг 7 из 9: Запись Кликов 🔴",
                message = "Кнопка 🔴 включает живую запись ваших тачей по экрану."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_8",
                title = "Шаг 8 из 9: Включение Джойстика",
                message = "Кнопка Джойстика откроет стик плавного управления движением."
            )
        )
        steps.add(
            TutorialStepConfig(
                id = "step_9",
                title = "Шаг 9 из 9: Сценарии 📁",
                message = "Кнопка Папки открывает сохранение и бэкап сценариев."
            )
        )

        currentStepIndex = 0
        isTutorialActive = true
        logDiagnostic("TUTORIAL", "Запущен последовательный туториал.")
        showCurrentStep()
    }

    fun nextStep() {
        if (!isTutorialActive) return
        currentStepIndex++
        if (currentStepIndex >= steps.size) {
            stopTutorial()
            return
        }
        showCurrentStep()
    }

    fun previousStep() {
        if (!isTutorialActive) return
        if (currentStepIndex > 0) {
            currentStepIndex--
            showCurrentStep()
        }
    }

    fun stopTutorial() {
        isTutorialActive = false
        currentStepIndex = 0
        service.overlayManager.tutorialOverlay.hide()
    }

    private fun showCurrentStep() {
        if (currentStepIndex in 0 until steps.size) {
            val step = steps[currentStepIndex]

            val targetButtonId = when (step.id) {
                "step_2" -> "btnPlay"
                "step_3" -> "btnAdd"
                "step_4" -> "btnCapturePool"
                "step_5" -> "btnHelpTutorial"
                "step_6" -> "btnToggleMenu"
                "step_7" -> "btnRecord"
                "step_8" -> "btnToggleJoystick"
                "step_9" -> "btnLoadScript"
                else -> ""
            }

            if (targetButtonId.isNotEmpty()) {
                getControlPanelChildBounds(service, targetButtonId) { exactBounds ->
                    val updatedStep = step.copy(highlightArea = exactBounds)
                    service.overlayManager.tutorialOverlay.show()
                    service.overlayManager.tutorialOverlay.renderStep(updatedStep)
                }
            } else {
                val panel = service.overlayManager.controlPanel
                val v = panel.overlayView
                val lp = panel.layoutParams
                val panelBounds = if (v != null && lp != null) {
                    val location = IntArray(2)
                    v.getLocationOnScreen(location)
                    Rect(location[0], location[1], location[0] + v.width, location[1] + v.height)
                } else Rect(100, 200, 500, 400)

                val updatedStep = step.copy(highlightArea = panelBounds)
                service.overlayManager.tutorialOverlay.show()
                service.overlayManager.tutorialOverlay.renderStep(updatedStep)
            }
        }
    }
}
