package com.example.autotap.ui.overlays

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class InfoHelpDialog(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_info_help

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        val tvInfo = view.findViewById<TextView>(R.id.tvInfoText)
        val btnClose = view.findViewById<Button>(R.id.btnInfoClose)

        val versionName = try {
            context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: "v40.0.0-PRO"
        } catch (_: Exception) {
            "v40.0.0-PRO"
        }

        val infoContent = "AutoTap PRO (" + versionName + ") — профессиональный инструмент автоматизации кликов.\n\n" +
                "Основные элементы:\n" +
                "• Панель управления — запуск, запись, загрузка сценариев.\n" +
                "• Джойстик — управление направлением и запись траектории.\n" +
                "• Зона захвата — область для поиска масок.\n" +
                "• Зона поиска ИИ — область для AI-сканера.\n" +
                "• Маркеры кликов — визуализация шагов сценария.\n" +
                "• Стоп-кнопка — мгновенная остановка сценария.\n\n" +
                "Сценарии:\n" +
                "• Каждый шаг — действие с координатами, задержкой и типом.\n" +
                "• Поддерживаются WAIT, CLICK, SWIPE, AI_SEARCH.\n" +
                "• Можно редактировать шаги через EditActionDialog.\n" +
                "• Можно сохранять, копировать, удалять сценарии.\n\n" +
                "AI-сканер:\n" +
                "• Ищет маски в зоне поиска.\n" +
                "• Маски редактируются через MaskEditorDialog.\n" +
                "• Поддерживает DPI-масштабирование.\n\n" +
                "Глобальные настройки:\n" +
                "• Длительность клика и свайпа.\n" +
                "• Пауза пред-скриншота.\n" +
                "• Защита от самоклика.\n\n" +
                "Overlay-архитектура v40:\n" +
                "• Все окна работают через OverlayBase.\n" +
                "• Все слои управляются OverlayManager.\n" +
                "• Все окна DPI-корректны и безопасны."

        tvInfo?.text = infoContent

        btnClose?.setOnClickListener {
            hide()
            logDiagnostic("UI", "Закрыта справка InfoHelpDialog.")
        }

        return view
    }
}
