package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class InfoHelpDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        width = 900
        height = 1200
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.7f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#EE1E1E2C"))
            setPadding(32, 32, 32, 32)
        }

        val title = TextView(context).apply {
            text = "📖 Руководство и Справка AutoTap v35/v37"
            setTextColor(Color.WHITE)
            textSize = 18f
            setPadding(0, 0, 0, 16)
        }
        root.addView(title)

        val scrollView = ScrollView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        }

        val helpContentText = TextView(context).apply {
            setTextColor(Color.parseColor("#DDDDDD"))
            textSize = 13f
            text = getHelpText()
        }
        scrollView.addView(helpContentText)
        root.addView(scrollView)

        val btnClose = Button(context).apply {
            text = "Понятно"
            setOnClickListener {
                logDiagnostic("UI", "Закрыта справка по работе приложения.")
                hide()
            }
        }
        root.addView(btnClose)

        return root
    }

    private fun getHelpText(): String {
        return """
        ⭐ ДОБРО ПОЖАЛОВАТЬ В AUTOTAP (v35/v37)
        Профессиональный комплекс авто-кликов, компьютерного зрения и записи сценариев.

        ══════════════════════════════════════════
        🧠 1. УМНАЯ МАСКА И ИИ-ПОИСК (CalibratedMask)
        • Авто-калибровка: При вырезании шаблона система вычисляет контуры (Sobel), выравнивает контраст (CLAHE) и удаляет фон.
        • Семейства масок (Profiles):
          - SMALL (иконки, крестики) — приоритетный поиск на 1.25x/1.4x.
          - MEDIUM (кнопки, карточки) — базовый поиск 1.0x.
          - LARGE (окна, панели) — ускоренный шаг каскада.
          - THIN_LINE (рамки, полоски HP) — поиск по Собель-градиентам.
        • Ручная калибровка: Кнопка «Калибровка маски» сбрасывает кэш и пересчитывает контуры.

        ══════════════════════════════════════════
        🔄 2. МУЛЬТИПОИСК (Continuous Multi-Search)
        • Поддержка нескольких масок на одном шаге.
        • Реактивный цикл: Захват снимка -> Поиск -> Клик -> Пауза -> СВЕЖИЙ снимок -> Повтор до нажатия СТОП.

        ══════════════════════════════════════════
        🎥 3. ЗАПИСЬ И ВОСПРОИЗВЕДЕНИЕ (Recording Engine)
        • Запись действий поверх оверлеев без перехвата чужих кликов.
        • Сохранение сценариев в формате JSON с нормализованными координатами.

        ══════════════════════════════════════════
        🎮 4. ИНТЕРАКТИВНЫЙ ДЖОЙСТИК (Joystick Control)
        • Движение Knob в 25 FPS с одновременным управлением и записью траектории.
        • Точное повторение recordedJoystickPath при воспроизведении.

        ══════════════════════════════════════════
        🛡️ 5. ЗАЩИТА ОТ САМО-НАЖАТИЙ (Anti-Self-Click)
        • Оверлеи используют FLAG_NOT_TOUCHABLE во время выполнения жестов.
        • Фильтр isOverlayArea() автоматически отменяет жесты, если они попадают в область UI-панелей.

        ══════════════════════════════════════════
        🎓 6. ИНТЕРАКТИВНОЕ ОБУЧЕНИЕ (Tutorial Engine)
        • Подсветка элементов экрана с эффектом PorterDuff.Mode.CLEAR и подсказками.

        ══════════════════════════════════════════
        📋 7. ДИАГНОСТИКА И ЛОГИ (StructuredLogger)
        • Миллисекундные штампы времени.
        • Авто-усечение файла error_log.txt при превышении 512 КБ.
        • Экран просмотра логов c функцией «Поделиться» через FileProvider.
        """.trimIndent()
    }
}
