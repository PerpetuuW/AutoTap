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
import com.example.autotap.getRealScreenSize
import com.example.autotap.logger.StructuredLogger
import com.example.autotap.model.ActionConfig
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayManager

class ScenarioDebuggerOverlay(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var statusText: TextView? = null
    private var ivPreview: ImageView? = null
    private var btnConfirm: Button? = null
    private var btnTrash: Button? = null
    private var currentTemplateIndex = -1
    private var detectedCandidate: MatchCandidate? = null

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
                text = "Калибровка ИИ-Маски"
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
                text = "Подтвердить маску"
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
                        StructuredLogger.logDiagnostic("CALIBRATION", "Маска #" + currentTemplateIndex + " удалена в корзину.")
                    }
                    overlayManager.candidateOverlay.hide()
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

    // 💥 КРИТИЧЕСКИЙ ФИКС: Принятие готового fullScreenBitmap (0 повторных запросов скриншота)
    fun startLiveCalibration(templateIndex: Int, directBitmap: Bitmap? = null, existingFullScreenBitmap: Bitmap? = null) {
        this.currentTemplateIndex = templateIndex
        this.detectedCandidate = null

        val svc = MyAutoClickService.instance ?: return
        val bitmap = directBitmap ?: svc.templateRepository.loadTemplate(templateIndex)

        if (bitmap == null) {
            StructuredLogger.logError("CALIBRATION", "Не удалось загрузить Bitmap Маски #" + templateIndex, null)
            Toast.makeText(context, " Ошибка загрузки Маски #" + templateIndex, Toast.LENGTH_SHORT).show()
            return
        }

        val runScanOnFrame = { frameBmp: Bitmap ->
            show()
            ivPreview?.setImageBitmap(bitmap)
            ivPreview?.visibility = View.VISIBLE

            StructuredLogger.logDiagnostic("CALIBRATION", "Мгновенный запуск ИИ-поиска на кадре (" + frameBmp.width + "x" + frameBmp.height + "px)...")
            statusText?.text = "Сканирование экрана для Маски #" + templateIndex + "...\nПоиск..."

            Thread {
                try {
                    val testAction = ActionConfig(
                        selectedTemplateIndex = templateIndex,
                        similarityPercent = 55,
                        customSearchArea = false
                    )
                    val scanResult = svc.aiScannerEngine.scan({ frameBmp }, testAction)
                    val candidates = scanResult.candidates

                    mainHandler.post {
                        if (candidates.isNotEmpty()) {
                            val top = candidates.first()
                            detectedCandidate = top
                            val percent = "" + (top.score * 100).toInt() + "%"
                            StructuredLogger.logDiagnostic("CALIBRATION", "🎯 Найдено совпадений: " + candidates.size + ". Лучшее: " + percent + " в точке (" + top.point.x + ", " + top.point.y + ")")
                            statusText?.text = "🎯 Найдено совпадений: " + candidates.size + " (" + percent + ")\nНажмите на нужный маяк на экране!"

                            overlayManager.candidateOverlay.showRadarBeaconCandidates(candidates) { confirmed ->
                                detectedCandidate = confirmed
                                StructuredLogger.logDiagnostic("CALIBRATION", "Пользователь выделил объект тапом по маяку: " + confirmed.point)
                                confirmSmartMaskGeneration()
                            }
                        } else {
                            StructuredLogger.logDiagnostic("CALIBRATION", "⚠️ Совпадений с точностью > 55% не найдено.")
                            statusText?.text = "Маска #" + templateIndex + " создана.\nОбъект не найден на экране. Подтвердите создание."
                        }
                    }
                } catch (e: Exception) {
                    StructuredLogger.logError("CALIBRATION", "Ошибка тестового сканирования калибровки", e)
                }
            }.start()
        }

        if (existingFullScreenBitmap != null && !existingFullScreenBitmap.isRecycled) {
            runScanOnFrame(existingFullScreenBitmap)
        } else {
            svc.captureScreenBitmapAsync { capturedBmp ->
                if (capturedBmp != null) {
                    runScanOnFrame(capturedBmp)
                } else {
                    StructuredLogger.logError("CALIBRATION", "Не удалось получить кадр при калибровке!", null)
                    show()
                    statusText?.text = "❌ Ошибка доступа к экрану.\nПерезапустите Спец. возможности!"
                }
            }
        }
    }

    private fun confirmSmartMaskGeneration() {
        val svc = MyAutoClickService.instance
        if (svc != null && currentTemplateIndex >= 0) {
            val calibrated = svc.templateRepository.recalibrateTemplate(currentTemplateIndex)
            val profile = calibrated?.metadata?.profile?.name ?: "MEDIUM"

            val matchedCandidate = detectedCandidate
            val recSim = if (matchedCandidate != null) {
                ((matchedCandidate.score * 100) - 5).toInt().coerceIn(60, 95)
            } else {
                calibrated?.metadata?.recommendedSimilarity ?: 85
            }

            if (svc.actionsList.isNotEmpty()) {
                val lastAction = svc.actionsList.last()
                lastAction.selectedTemplateIndex = currentTemplateIndex
                lastAction.similarityPercent = recSim
                if (matchedCandidate != null) {
                    val screenSize = context.getRealScreenSize()
                    lastAction.xNorm = (matchedCandidate.point.x / screenSize.x).coerceIn(0f, 1f)
                    lastAction.yNorm = (matchedCandidate.point.y / screenSize.y).coerceIn(0f, 1f)
                }
                StructuredLogger.logDiagnostic("CALIBRATION", "Обновлены параметры шага: selectedTemplateIndex=" + currentTemplateIndex + ", similarityPercent=" + recSim + ", pos=(" + lastAction.xNorm + ", " + lastAction.yNorm + ")")
            }

            Toast.makeText(
                context,
                "Маска #" + currentTemplateIndex + " откалибрована! Профиль: " + profile + " (" + recSim + "%)",
                Toast.LENGTH_LONG
            ).show()
        }
        overlayManager.candidateOverlay.hide()
        hide()
    }

    fun showCalibratedTemplate(bitmap: Bitmap, templateIndex: Int, profileName: String, widthPx: Int, heightPx: Int, existingFullScreenBitmap: Bitmap? = null) {
        startLiveCalibration(templateIndex, bitmap, existingFullScreenBitmap)
    }

    fun showCandidates(candidates: List<MatchCandidate>) {
        if (candidates.isEmpty()) {
            showNoMatch()
            return
        }
        show()
        val topCandidate = candidates.first()
        val scorePercent = "" + (topCandidate.score * 100).toInt() + "%"
        statusText?.text = "Найден объект: точность " + scorePercent + "\nПодтвердите выбор объекта"
        ivPreview?.visibility = View.GONE

        mainHandler.removeCallbacksAndMessages(null)
        mainHandler.postDelayed({ hide() }, 2500L)
    }

    fun showNoMatch() {
        show()
        statusText?.text = "ИИ Поиск: совпадений не найдено"
        ivPreview?.visibility = View.GONE

        mainHandler.removeCallbacksAndMessages(null)
        mainHandler.postDelayed({ hide() }, 2000L)
    }

    override fun hide() {
        mainHandler.removeCallbacksAndMessages(null)
        super.hide()
    }
}
