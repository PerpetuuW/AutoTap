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
    private var lastCapturedIndex = -1

    private val autoHideHandler = Handler(Looper.getMainLooper())

    init {
        width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        initialY = 100.dpToPx(context)
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

            // Равновесная строка кнопок без обрезки текста
            val btnRow = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
                setPadding(0, 12, 0, 0)
            }

            btnConfirm = Button(context).apply {
                text = "✅ Понятно"
                textSize = 12f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#1F6FEB"))
                setTextColor(Color.WHITE)
                setPadding(16, 0, 16, 0)
                setOnClickListener { hide() }
            }

            btnTrash = Button(context).apply {
                text = "🗑 В корзину"
                textSize = 12f
                setTypeface(null, Typeface.BOLD)
                setBackgroundColor(Color.parseColor("#F04438"))
                setTextColor(Color.WHITE)
                setPadding(16, 0, 16, 0)
                setOnClickListener {
                    if (lastCapturedIndex >= 0) {
                        MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(lastCapturedIndex)
                    }
                    hide()
                }
            }

            val btnLp = LinearLayout.LayoutParams(0, 44.dpToPx(context), 1.0f)
            btnRow.addView(btnConfirm, btnLp)
            btnRow.addView(View(context), LinearLayout.LayoutParams(12.dpToPx(context), 1))
            btnRow.addView(btnTrash, btnLp)
            addView(btnRow, LinearLayout.LayoutParams(260.dpToPx(context), LinearLayout.LayoutParams.WRAP_CONTENT))
        }

        return root
    }

    fun showCalibratedTemplate(bitmap: Bitmap, templateIndex: Int, profileName: String, widthPx: Int, heightPx: Int) {
        this.lastCapturedIndex = templateIndex
        show()

        ivPreview?.setImageBitmap(bitmap)
        ivPreview?.visibility = View.VISIBLE

        statusText?.text = "🎯 Маска #$templateIndex откалибрована!\nРазмер: ${widthPx}x${heightPx}px | Профиль: $profileName"
        logAppEvent("AI_SCANNER", "Показан объект калибровки маски #$templateIndex (${widthPx}x${heightPx}px)")

        autoHideHandler.removeCallbacksAndMessages(null)
        autoHideHandler.postDelayed({ hide() }, 5000L)
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        if (candidates.isEmpty()) {
            showNoMatch()
            return
        }
        val topCandidate = candidates.first()
        val scorePercent = "${(topCandidate.score * 100).toInt()}%"
        statusText?.text = "🎯 Маска #${topCandidate.templateIndex} найдена: $scorePercent точность"
        logAppEvent("AI_SCANNER", "ИИ нашел совпадение: Маска #${topCandidate.templateIndex}, точность: $scorePercent")

        autoHideHandler.removeCallbacksAndMessages(null)
        autoHideHandler.postDelayed({ hide() }, 2500L)
    }

    fun showNoMatch() {
        statusText?.text = "🔍 ИИ Поиск: совпадений не найдено"
        ivPreview?.visibility = View.GONE
        logAppEvent("AI_SCANNER", "Debugger: NO MATCH")

        autoHideHandler.removeCallbacksAndMessages(null)
        autoHideHandler.postDelayed({ hide() }, 2000L)
    }

    override fun hide() {
        autoHideHandler.removeCallbacksAndMessages(null)
        super.hide()
    }
}
