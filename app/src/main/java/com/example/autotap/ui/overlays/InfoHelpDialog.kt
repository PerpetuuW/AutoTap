package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class InfoHelpDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var tvContent: TextView? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.7f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_info, null)

        tvContent = view.findViewByNames("tvTabContent") as? TextView

        val versionName = try {
            context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: context.getString(R.string.app_version)
        } catch (_: Exception) {
            context.getString(R.string.app_version)
        }

        tvContent?.text = "AutoTap PRO (" + versionName + ")

Справка по автоматизации и ИИ-поиску масок."

        view.bindClickByNames("tabClick") {
            tvContent?.text = "Справка по Кликам:
• Длительность настраивается от 10мс до 1000мс.
• Доступна случайная координатная погрешность (джиттер)."
            logDiagnostic("UI", "Переключение таба CLICK в InfoHelpDialog.")
        }

        view.bindClickByNames("tabSwipe") {
            tvContent?.text = "Справка по Свайпам:
• Плавные свайпы и траектории джойстика с частотой 25 FPS.
• Отображение стартового и конечного маркеров."
            logDiagnostic("UI", "Переключение таба SWIPE в InfoHelpDialog.")
        }

        view.bindClickByNames("tabAi") {
            tvContent?.text = "Справка по ИИ-Поиску (" + versionName + "):
• Семейства масок: Small, Medium, Large, Thin-Line.
• Реактивный мультипоиск со свежими кадрами экрана."
            logDiagnostic("UI", "Переключение таба AI в InfoHelpDialog.")
        }

        view.bindClickByNames("btnCloseInfoDialog") {
            logDiagnostic("UI", "Закрыта справка btnCloseInfoDialog.")
            hide()
        }

        return view
    }
}
