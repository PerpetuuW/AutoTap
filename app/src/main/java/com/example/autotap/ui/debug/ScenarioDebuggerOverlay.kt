package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Typeface
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.dpToPx
import com.example.autotap.engine.ai.MatchCandidate
import com.example.autotap.logAppEvent
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null
    private var ivPreview: ImageView? = null
    private var btnConfirm: Button? = null
    private var btnTrash: Button? = null
    private var currentTemplateIndex = -1

    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        initialY = 90.dpToPx(context)
    }

    override fun createView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundResource(R.drawable.panel_background)
            setPadding(24, 16, 24, 16)

            val tv = TextView(context).apply {
                text = "🎯 Калибровка ИИ-Маски"
                setTextColor(Color.parseColor("#00F5D4"))
                textSize = 14f
                setTypeface(null, Typeface.BOLD)
                gravity = Gravity.CENTER
            }
            statusText = tv
            addView(tv)

            val img = ImageView(context).apply {
                visibility = View.GONE
                setPadding(0, 10, 0, 10)
            }
            ivPreview = img
            addView(img, LinearLayout.LayoutParams(120.dpToPx(context), 120.dpToPx(context)))

            val btnRow = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
                setPadding(0, 12, 0, 0)
            }

            btnConfirm = Button(context).apply {
                text = "Подтвердить объект"
                textSize = 11f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#1F6FEB"))
                setTextColor(Color.WHITE)
                setOnClickListener {
                    confirmSmartMaskGeneration()
                }
            }

            btnTrash = Button(context).apply {
                text = "Удалить в корзину"
                textSize = 11f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#2A1215"))
                setTextColor(Color.parseColor("#FF5B5B"))
                setOnClickListener {
                    if (currentTemplateIndex >= 0) {
                        MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(currentTemplateIndex)
                    }
                    hide()
                }
            }

            val btnLp = LinearLayout.LayoutParams(0, 44.dpToPx(context), 1.0f)
            btnRow.addView(btnConfirm, btnLp)
            btnRow.addView(View(context), LinearLayout.LayoutParams(10.dpToPx(context), 1))
            btnRow.addView(btnTrash, btnLp)
            addView(btnRow, LinearLayout.LayoutParams(270.dpToPx(context), LinearLayout.LayoutParams.WRAP_CONTENT))
        }

        return root
    }

    fun startLiveCalibration(templateIndex: Int, directBitmap: Bitmap? = null) {
        this.currentTemplateIndex = templateIndex
        show()

        val svc = MyAutoClickService.instance ?: return
        val bitmap = directBitmap ?: svc.templateRepository.loadTemplate(templateIndex)

        if (bitmap != null) {
            ivPreview?.setImageBitmap(bitmap)
            ivPreview?.visibility = View.VISIBLE
            statusText?.text = "Сканирование экрана для Маски #$templateIndex...\nПодтвердите найденный объект"
        } else {
            statusText?.text = "Ошибка загрузки маски #$templateIndex"
        }
    }

    private fun confirmSmartMaskGeneration() {
        val svc = MyAutoClickService.instance
        if (svc != null && currentTemplateIndex >= 0) {
            val calibrated = svc.templateRepository.recalibrateTemplate(currentTemplateIndex)
            val profile = calibrated?.metadata?.profile?.name ?: "MEDIUM"
            val recSim = calibrated?.metadata?.recommendedSimilarity ?: 85

            Toast.makeText(
                context,
                "Умная маска #$currentTemplateIndex создана! Профиль: $profile (Порог: $recSim%)",
                Toast.LENGTH_LONG
            ).show()
            logAppEvent("AI_SCANNER", "Умная маска #$currentTemplateIndex сгенерирована.")
        }
        hide()
    }

    fun showCalibratedTemplate(bitmap: Bitmap, templateIndex: Int, profileName: String, widthPx: Int, heightPx: Int) {
        startLiveCalibration(templateIndex, bitmap)
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        if (candidates.isEmpty()) {
            showNoMatch()
            return
        }
        show()
        val topCandidate = candidates.first()
        val scorePercent = "${(topCandidate.score * 100).toInt()}%"
        statusText?.text = "Найден объект: точность $scorePercent\nПодтвердите выбор объекта"
        ivPreview?.visibility = View.GONE
        logAppEvent("AI_SCANNER", "ИИ нашел совпадение: Маска #${topCandidate.templateIndex}, точность: $scorePercent")

        mainHandler.removeCallbacksAndMessages(null)
        mainHandler.postDelayed({ hide() }, 2500L)
    }

    fun showNoMatch() {
        show()
        statusText?.text = "ИИ Поиск: совпадений не найдено"
        ivPreview?.visibility = View.GONE
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")

        mainHandler.removeCallbacksAndMessages(null)
        mainHandler.postDelayed({ hide() }, 2000L)
    }

    override fun hide() {
        mainHandler.removeCallbacksAndMessages(null)
        super.hide()
    }
}
