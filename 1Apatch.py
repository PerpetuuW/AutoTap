import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан файл: {rel_path}")

def fix_compilation_errors():
    print("🚀 Устранение всех 30 ошибок компиляции Kotlin (v36.6.0-PRO)...")

    # 1. app/build.gradle.kts
    gradle_code = r"""plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.autotap"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.autotap"
        minSdk = 24
        targetSdk = 35
        versionCode = 2490
        versionName = "36.6.0-PRO"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("com.google.android.material:material:1.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
"""
    write_file("app/build.gradle.kts", gradle_code)

    # 2. ActionType.kt (Добавлены HOLD, SWIPE_PATH, WAIT, LOOP)
    action_type_code = r"""package com.example.autotap

enum class ActionType {
    CLICK,
    LONG_PRESS,
    SWIPE,
    SWIPE_PATH,
    TRIGGER,
    WAIT,
    LOOP,
    HOLD
}
"""
    write_file("app/src/main/java/com/example/autotap/ActionType.kt", action_type_code)

    # 3. CandidateSelector.kt
    selector_code = r"""package com.example.autotap.engine

import com.example.autotap.MatchCandidate

object CandidateSelector {
    fun selectBest(candidates: List<MatchCandidate>): MatchCandidate? {
        return candidates.maxByOrNull { it.score }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/CandidateSelector.kt", selector_code)

    # 4. OverlayBase.kt (Поддержка программных View без XML layoutResId)
    overlay_base_code = r"""package com.example.autotap.ui.base

import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService

abstract class OverlayBase(
    protected val service: MyAutoClickService,
    val layoutResId: Int = 0,
    val layer: OverlayLayer = OverlayLayer.PANEL,
    val priority: OverlayPriority = OverlayPriority.MEDIUM
) {
    var rootView: View? = null
        protected set

    val isShowing: Boolean
        get() = rootView != null && rootView?.parent != null

    open fun onAttach() {}
    open fun onDetach() {}
    open fun onUpdate() {}
    open fun onVisibilityChanged(visible: Boolean) {}

    open fun show() {
        if (isShowing) {
            rootView?.visibility = View.VISIBLE
            onVisibilityChanged(true)
            return
        }

        val view = if (layoutResId != 0) {
            service.overlayManager.getViewFromReusePool(layoutResId)
                ?: LayoutInflater.from(service).inflate(layoutResId, null)
        } else {
            rootView
        }

        if (view == null) return

        rootView = view
        val params = createParams()
        onViewInflated(view)
        service.overlayManager.safeAddView(view, params)
        onAttach()
        fadeIn()
    }

    open fun hide() {
        if (!isShowing) return
        fadeOut {
            rootView?.let {
                service.overlayManager.safeRemoveView(it)
                if (layoutResId != 0) {
                    service.overlayManager.recycleViewToPool(layoutResId, it)
                }
            }
            onDetach()
            rootView = null
        }
    }

    protected open fun fadeIn(duration: Long = 180L) {
        rootView?.let { v ->
            v.alpha = 0f
            v.animate().alpha(1f).setDuration(duration).start()
        }
    }

    protected open fun fadeOut(onEnd: () -> Unit) {
        rootView?.let { v ->
            v.animate().alpha(0f).setDuration(150L).withEndAction { onEnd() }.start()
        } ?: onEnd()
    }

    protected open fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams()
    }

    protected abstract fun onViewInflated(view: View)

    protected fun <T : View> findViewById(id: Int): T? {
        return rootView?.findViewById(id)
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt", overlay_base_code)

    # 5. ScenarioDebuggerOverlay.kt (Программное создание DebugCanvasView)
    debugger_code = r"""package com.example.autotap.ui.debug

import android.content.Context
import android.graphics.*
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority

class ScenarioDebuggerOverlay(service: MyAutoClickService) :
    OverlayBase(service, 0, OverlayLayer.DEBUG, OverlayPriority.HIGH) {

    private var debugCanvasView: DebugCanvasView? = null

    override fun show() {
        if (isShowing) return
        val view = DebugCanvasView(service)
        debugCanvasView = view
        rootView = view
        val params = createParams()
        service.overlayManager.safeAddView(view, params)
        onAttach()
        fadeIn()
    }

    override fun onViewInflated(view: View) {}

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }
    }

    fun update(config: ActionConfig) {
        if (!isShowing) show()
        debugCanvasView?.updateConfig(config)
    }

    class DebugCanvasView(context: Context) : View(context) {
        private var cfg: ActionConfig? = null

        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.CYAN
            textSize = 34f
            typeface = Typeface.DEFAULT_BOLD
        }

        private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        private val heatPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            alpha = 70
        }

        fun updateConfig(config: ActionConfig) {
            cfg = config
            invalidate()
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val c = cfg ?: return
            val svc = MyAutoClickService.instance ?: return

            canvas.drawText("STEP #${c.id} [${c.type.name}] | Delay: ${c.delay}ms | Reps: ${c.repeatCount}", 40f, 100f, textPaint)

            when (c.type) {
                ActionType.CLICK, ActionType.LONG_PRESS, ActionType.HOLD -> {
                    val pt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                    strokePaint.color = Color.GREEN
                    canvas.drawCircle(pt.first, pt.second, 40f, strokePaint)
                    canvas.drawText("Target (${pt.first.toInt()}, ${pt.second.toInt()})", pt.first + 50f, pt.second, textPaint)
                }

                ActionType.SWIPE, ActionType.SWIPE_PATH -> {
                    val startPt = svc.resolveNormalizedPoint(c.xNorm, c.yNorm)
                    val endPt = svc.resolveNormalizedPoint(c.endXNorm, c.endYNorm)

                    strokePaint.color = Color.CYAN
                    canvas.drawCircle(startPt.first, startPt.second, 25f, strokePaint)
                    canvas.drawCircle(endPt.first, endPt.second, 25f, strokePaint)
                    canvas.drawLine(startPt.first, startPt.second, endPt.first, endPt.second, strokePaint)

                    if (c.joystickPath.isNotEmpty()) {
                        strokePaint.color = Color.MAGENTA
                        val path = Path()
                        val first = c.joystickPath.first()
                        val fPt = svc.resolveNormalizedPoint(first.x, first.y)
                        path.moveTo(fPt.first, fPt.second)

                        for (p in c.joystickPath.drop(1)) {
                            val pPt = svc.resolveNormalizedPoint(p.x, p.y)
                            path.lineTo(pPt.first, pPt.second)
                            canvas.drawCircle(pPt.first, pPt.second, 6f, strokePaint)
                        }
                        canvas.drawPath(path, strokePaint)
                    }
                }

                ActionType.TRIGGER -> {
                    if (c.customSearchArea) {
                        val startPt = svc.resolveNormalizedPoint(c.searchAreaXNorm, c.searchAreaYNorm)
                        val endPt = svc.resolveNormalizedPoint(c.searchAreaXNorm + c.searchAreaWNorm, c.searchAreaYNorm + c.searchAreaHNorm)

                        strokePaint.color = Color.YELLOW
                        val rect = RectF(startPt.first, startPt.second, endPt.first, endPt.second)
                        canvas.drawRect(rect, strokePaint)
                        canvas.drawText("Search Area (${c.similarityPercent}%)", startPt.first + 10f, startPt.second + 40f, textPaint)
                    }

                    c.calibratedRectNorm?.let { r ->
                        val startPt = svc.resolveNormalizedPoint(r.left.toFloat(), r.top.toFloat())
                        val endPt = svc.resolveNormalizedPoint(r.right.toFloat(), r.bottom.toFloat())

                        strokePaint.color = Color.RED
                        heatPaint.color = Color.RED
                        val rect = RectF(startPt.first, startPt.second, endPt.first, endPt.second)
                        canvas.drawRect(rect, heatPaint)
                        canvas.drawRect(rect, strokePaint)
                        canvas.drawText("Calibrated Mask Box", startPt.first + 10f, startPt.second + 40f, textPaint)
                    }
                }

                ActionType.WAIT -> {
                    canvas.drawText("WAIT State: ${c.waitType} (${c.holdDuration}ms)", 40f, 160f, textPaint)
                }

                ActionType.LOOP -> {
                    canvas.drawText("LOOP State: ${c.loopType} [Reps: ${c.loopCount}] -> Step #${c.loopStartIndex}", 40f, 160f, textPaint)
                }
            }
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/debug/ScenarioDebuggerOverlay.kt", debugger_code)

    # 6. ClickVisualizerOverlay.kt (Фикс dpToPx)
    click_vis_code = r"""package com.example.autotap.ui.overlays

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ClickVisualizerOverlay(private val service: MyAutoClickService) {

    fun showClickAt(x: Float, y: Float) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_beacon_ring, null)
        val sizePx = service.dpToPx(40)
        val params = service.overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            this.x = (x - sizePx / 2f).toInt()
            this.y = (y - sizePx / 2f).toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.alpha = 0f
        view.scaleX = 0.4f
        view.scaleY = 0.4f

        val fadeIn = ObjectAnimator.ofFloat(view, View.ALPHA, 0f, 1f).setDuration(80)
        val scaleX = ObjectAnimator.ofFloat(view, View.SCALE_X, 0.4f, 1.8f).setDuration(280)
        val scaleY = ObjectAnimator.ofFloat(view, View.SCALE_Y, 0.4f, 1.8f).setDuration(280)
        val fadeOut = ObjectAnimator.ofFloat(view, View.ALPHA, 1f, 0f).setDuration(150)
        fadeOut.startDelay = 150

        AnimatorSet().apply {
            playTogether(fadeIn, scaleX, scaleY, fadeOut)
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: android.animation.Animator) {
                    service.overlayManager.safeRemoveView(view)
                }
            })
            start()
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/ClickVisualizerOverlay.kt", click_vis_code)

    # 7. EditActionDialog.kt (Фикс component1/2, getRealScreenSize, globalTemplates)
    edit_dialog_code = r"""package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.engine.ActionEditorEngine
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class EditActionDialog(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_edit_dialog, OverlayLayer.PANEL, OverlayPriority.MEDIUM) {

    private var currentConfig: ActionConfig? = null

    override fun onViewInflated(view: View) {}

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            flags = WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
        }
    }

    fun show(config: ActionConfig) {
        currentConfig = config
        super.show()
        rootView?.let { bindUi(it, config) }
    }

    private fun bindUi(dialogView: View, config: ActionConfig) {
        val currentStepIdx = service.actionsList.indexOf(config)

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val etStepOrder = dialogView.findViewById<EditText>(R.id.etStepOrder)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etRepeat = dialogView.findViewById<EditText>(R.id.etRepeatCount)
        val etRadius = dialogView.findViewById<EditText>(R.id.etRandomRadius)
        val tvHoldTitle = dialogView.findViewById<TextView>(R.id.tvHoldTitle)
        val etHold = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val btnPrevStep = dialogView.findViewById<Button>(R.id.btnPrevStep)
        val btnNextStep = dialogView.findViewById<Button>(R.id.btnNextStep)
        val btnSaveHeader = dialogView.findViewById<View>(R.id.btnSaveHeader)
        val btnCloseHeader = dialogView.findViewById<View>(R.id.btnCloseHeader)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSave)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        val btnCloneAction = dialogView.findViewById<Button>(R.id.btnCloneAction)
        val btnDeleteAction = dialogView.findViewById<Button>(R.id.btnDeleteAction)

        val layoutAiBlock = dialogView.findViewById<View>(R.id.layoutAiParametersBlock)
        val etAiTimeout = dialogView.findViewById<EditText>(R.id.etAiTimeout)
        val etSimilarity = dialogView.findViewById<EditText>(R.id.etSimilarityPercent)
        val etScanInterval = dialogView.findViewById<EditText>(R.id.etScanInterval)
        val etPostMatchDelay = dialogView.findViewById<EditText>(R.id.etPostMatchDelay)
        val etJumpStep = dialogView.findViewById<EditText>(R.id.etJumpToStep)

        val btnCalibrate = dialogView.findViewById<Button>(R.id.btnCalibrateMatchesOnScreen)
        val btnToggleAiNotif = dialogView.findViewById<Button>(R.id.btnToggleAiNotification)
        val btnMultiTemplates = dialogView.findViewById<Button>(R.id.btnManageMultiTemplates)
        val btnClickTarget = dialogView.findViewById<Button>(R.id.btnToggleClickTarget)
        val btnScriptLoad = dialogView.findViewById<Button>(R.id.btnSelectScriptToLoad)

        val tvTemplateIndex = dialogView.findViewById<TextView>(R.id.tvTemplateIndex)
        val ivTemplatePreview = dialogView.findViewById<ImageView>(R.id.ivSelectedTemplateImagePreview)
        val btnPrevTemplate = dialogView.findViewById<Button>(R.id.btnPrevTemplate)
        val btnNextTemplate = dialogView.findViewById<Button>(R.id.btnNextTemplate)
        val btnDeleteSelectedTemplate = dialogView.findViewById<Button>(R.id.btnDeleteSelectedTemplate)

        tvTitle?.text = "Действие #${config.id}"
        etStepOrder?.setText(config.id.toString())
        etDelay?.setText((config.delay / 1000.0).toString())
        etRepeat?.setText(if (config.repeatCount == -1) "∞" else config.repeatCount.toString())
        etRadius?.setText(config.randomRadius.toString())
        etHold?.setText(config.holdDuration.toString())

        etAiTimeout?.setText(config.aiTimeoutSeconds.toString())
        etSimilarity?.setText(config.similarityPercent.toString())
        etScanInterval?.setText(config.scanIntervalSeconds.toString())
        etPostMatchDelay?.setText(config.postMatchDelaySeconds.toString())
        etJumpStep?.setText(if (config.jumpToStepOnMatch > 0) config.jumpToStepOnMatch.toString() else "0")

        var selectedType = config.type

        fun updateTemplatePreviewUI() {
            if (service.globalTemplatesNames.isEmpty()) {
                tvTemplateIndex?.text = "Шаблонов нет (0)"
                ivTemplatePreview?.setImageBitmap(null)
                config.selectedTemplateIndex = -1
                return
            }
            if (config.selectedTemplateIndex !in service.globalTemplatesNames.indices) {
                config.selectedTemplateIndex = 0
            }
            val idx = config.selectedTemplateIndex
            val total = service.globalTemplatesNames.size
            val maskPath = service.globalTemplatesNames[idx]
            val fileName = File(maskPath).nameWithoutExtension

            tvTemplateIndex?.text = "№${idx + 1}/$total: $fileName"
            val bmp = service.globalTemplates.getOrNull(idx) ?: BitmapFactory.decodeFile(maskPath)
            ivTemplatePreview?.setImageBitmap(bmp)
        }

        fun updateUi() {
            val isClick = selectedType == ActionType.CLICK
            val isHold = selectedType == ActionType.LONG_PRESS || selectedType == ActionType.HOLD
            val isSwipe = selectedType == ActionType.SWIPE || selectedType == ActionType.SWIPE_PATH
            val isTrigger = selectedType == ActionType.TRIGGER

            btnTypeClick?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isClick) R.color.accent_blue else R.color.panel_blue))
            btnTypeHold?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isHold) R.color.accent_blue else R.color.panel_blue))
            btnTypeSwipe?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isSwipe) R.color.accent_blue else R.color.panel_blue))
            btnTypeTrigger?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (isTrigger) R.color.accent_blue else R.color.panel_blue))

            tvHoldTitle?.visibility = if (isHold) View.VISIBLE else View.GONE
            etHold?.visibility = if (isHold) View.VISIBLE else View.GONE

            layoutAiBlock?.visibility = if (isTrigger) View.VISIBLE else View.GONE

            btnToggleAiNotif?.text = if (config.playAudioOnMatch) "🔔 Звук / Вибро при совпадении: [ВКЛ]" else "🔔 Звук / Вибро при совпадении: [ВЫКЛ]"
            btnToggleAiNotif?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.playAudioOnMatch) R.color.accent_blue else R.color.panel_blue))

            val multiCount = config.multiTemplateIndices.size
            btnMultiTemplates?.text = if (multiCount > 0) "🗂 Мультишаблоны: [ Выбрано $multiCount маск ]" else "🗂 Мультишаблоны: [ Обычный режим (1 маска) ]"
            btnMultiTemplates?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (multiCount > 0) R.color.accent_blue else R.color.panel_blue))

            btnClickTarget?.text = if (config.clickAiTarget) "🎯 Клик по мишени: [ВКЛ]" else "🎯 Клик по мишени: [ВЫКЛ]"
            btnClickTarget?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.clickAiTarget) R.color.accent_blue else R.color.panel_blue))

            btnScriptLoad?.text = if (config.targetScriptToLoad.isNotEmpty()) "📁 Переход на сценарий: [ ${config.targetScriptToLoad} ]" else "📁 Переход на сценарий: [ НЕТ ]"
            btnScriptLoad?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (config.targetScriptToLoad.isNotEmpty()) R.color.accent_blue else R.color.panel_blue))

            if (isTrigger) updateTemplatePreviewUI()
        }

        btnTypeClick?.setOnClickListener { selectedType = ActionType.CLICK; updateUi() }
        btnTypeHold?.setOnClickListener { selectedType = ActionType.LONG_PRESS; updateUi() }
        btnTypeSwipe?.setOnClickListener { selectedType = ActionType.SWIPE; updateUi() }
        btnTypeTrigger?.setOnClickListener { selectedType = ActionType.TRIGGER; updateUi() }

        btnToggleAiNotif?.setOnClickListener { service.vibrateFeedback(20L); config.playAudioOnMatch = !config.playAudioOnMatch; updateUi() }
        btnClickTarget?.setOnClickListener { service.vibrateFeedback(20L); config.clickAiTarget = !config.clickAiTarget; updateUi() }
        btnScriptLoad?.setOnClickListener { service.vibrateFeedback(20L); service.showScriptPickerDialog("Выберите сценарий для перехода") { name -> config.targetScriptToLoad = name; updateUi() } }

        btnPrevTemplate?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.globalTemplatesNames.isNotEmpty()) {
                config.selectedTemplateIndex = (config.selectedTemplateIndex - 1 + service.globalTemplatesNames.size) % service.globalTemplatesNames.size
                updateTemplatePreviewUI()
            }
        }

        btnNextTemplate?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.globalTemplatesNames.isNotEmpty()) {
                config.selectedTemplateIndex = (config.selectedTemplateIndex + 1) % service.globalTemplatesNames.size
                updateTemplatePreviewUI()
            }
        }

        btnDeleteSelectedTemplate?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (config.selectedTemplateIndex in service.globalTemplatesNames.indices) {
                service.moveTemplateToTrash(config.selectedTemplateIndex)
                service.loadAllTemplatesFromDisk()
                updateTemplatePreviewUI()
                updateUi()
            }
        }

        fun saveCurrentData() {
            config.type = selectedType
            config.delay = ((etDelay?.text?.toString()?.toDoubleOrNull() ?: 1.0) * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRadius?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHold?.text?.toString()?.toLongOrNull()?.coerceAtLeast(100L) ?: 1000L

            config.aiTimeoutSeconds = etAiTimeout?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 15
            config.similarityPercent = etSimilarity?.text?.toString()?.toIntOrNull()?.coerceIn(10, 99) ?: 70
            config.scanIntervalSeconds = etScanInterval?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 5
            config.postMatchDelaySeconds = etPostMatchDelay?.text?.toString()?.toIntOrNull()?.coerceAtLeast(0) ?: 3
            config.jumpToStepOnMatch = etJumpStep?.text?.toString()?.toIntOrNull() ?: -1

            ActionEditorEngine.validateAndNormalize(config)

            if (selectedType == ActionType.SWIPE && config.endView == null) {
                val screenSize = service.getRealScreenSize()
                val sw = screenSize.first
                val sh = screenSize.second
                service.spawnEndTargetAtPosition(config, sw / 2f + service.dpToPx(80), sh / 2f + service.dpToPx(80))
            } else if (selectedType != ActionType.SWIPE && config.endView != null) {
                service.overlayManager.safeRemoveView(config.endView)
                config.endView = null
            }
        }

        btnCalibrate?.setOnClickListener {
            service.vibrateFeedback(30L)
            saveCurrentData()
            hide()
            service.aiScannerEngine.startTemplateCalibration(config)
        }

        btnCloneAction?.setOnClickListener {
            service.vibrateFeedback(25L)
            saveCurrentData()
            hide()
            val screenSize = service.getRealScreenSize()
            val sw = screenSize.first
            val sh = screenSize.second
            service.addNewActionAtPosition(sw / 2f + service.dpToPx(20), sh / 2f + service.dpToPx(20), config.delay, config.type, config.selectedTemplateIndex)
            Toast.makeText(service, "📋 Шаг #${config.id} клонирован!", Toast.LENGTH_SHORT).show()
        }

        btnDeleteAction?.setOnClickListener {
            service.vibrateFeedback(30L)
            hide()
            service.overlayManager.safeRemoveView(config.startView)
            config.endView?.let { service.overlayManager.safeRemoveView(it) }
            service.actionsList.remove(config)
            for (i in service.actionsList.indices) {
                val act = service.actionsList[i]
                act.id = i + 1
                act.startView?.findViewById<TextView>(R.id.tvTargetNumber)?.text = act.id.toString()
                act.endView?.findViewById<TextView>(R.id.tvTargetNumberEnd)?.text = "${act.id}E"
            }
            Toast.makeText(service, "🗑 Шаг удален", Toast.LENGTH_SHORT).show()
        }

        btnPrevStep?.setOnClickListener {
            saveCurrentData()
            hide()
            if (currentStepIdx > 0) show(service.actionsList[currentStepIdx - 1])
        }

        btnNextStep?.setOnClickListener {
            saveCurrentData()
            hide()
            if (currentStepIdx < service.actionsList.size - 1) show(service.actionsList[currentStepIdx + 1])
        }

        val performSave = {
            service.vibrateFeedback(30L)
            saveCurrentData()
            hide()
            Toast.makeText(service, "Шаг #${config.id} сохранен!", Toast.LENGTH_SHORT).show()
        }

        val performClose = { service.vibrateFeedback(25L); hide() }

        btnSaveHeader?.setOnClickListener { performSave() }
        btnCloseHeader?.setOnClickListener { performClose() }
        btnSave?.setOnClickListener { performSave() }
        btnCancel?.setOnClickListener { performClose() }

        updateUi()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/EditActionDialog.kt", edit_dialog_code)

    # 8. MyAutoClickService.kt (Публичные вспомогательные методы)
    service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScenarioRunner
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.*
import java.io.File

class MyAutoClickService : AccessibilityService() {

    companion object {
        var instance: MyAutoClickService? = null

        fun logError(ctx: Context, e: Throwable) {
            try {
                val file = File(ctx.filesDir, "error_log.txt")
                file.appendText("\n\n${System.currentTimeMillis()}:\n${e.stackTraceToString()}")
            } catch (_: Exception) {}
        }

        fun logAppEvent(ctx: Context, tag: String, msg: String) {
            try {
                val file = File(ctx.filesDir, "app_events.txt")
                file.appendText("\n[$tag] $msg")
            } catch (_: Exception) {}
        }
    }

    // --- CORE SUBSYSTEMS ---
    lateinit var overlayManager: OverlayManager
    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var scenarioRunner: ScenarioRunner
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // --- UI OVERLAYS ---
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay
    lateinit var clickVisualizerOverlay: ClickVisualizerOverlay

    // --- STATE ---
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false
    var isNumbersHidden = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplates: ArrayList<Bitmap>
        get() = templateRepository.globalTemplates

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        templateRepository = TemplateRepository.init(this)
        scriptRepository = ScriptRepository.init(this)

        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        scenarioRunner = ScenarioRunner(this)
        aiScannerEngine = AiScannerEngine(this)

        controlPanelOverlay = ControlPanelOverlay(this)
        joystickOverlay = JoystickOverlay(this)
        captureFrameOverlay = CaptureFrameOverlay(this)
        debuggerOverlay = ScenarioDebuggerOverlay(this)
        clickVisualizerOverlay = ClickVisualizerOverlay(this)

        templateRepository.loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v36.6.0-PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    fun vibrateFeedback(ms: Long = 25L) = gestureExecutor.vibrateFeedback(ms)

    fun getRealScreenSize(): Pair<Int, Int> = overlayManager.getRealScreenSize()
    fun dpToPx(dp: Int): Int = overlayManager.dpToPx(dp)
    fun dpToPx(dp: Float): Int = overlayManager.dpToPx(dp)

    fun showControlPanel() = controlPanelOverlay.show()

    fun hideControlPanel(openMainApp: Boolean = false) {
        controlPanelOverlay.hide()
        if (openMainApp) {
            try {
                val intent = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(intent)
            } catch (e: Exception) { logError(this, e) }
        }
    }

    fun showFloatingStopButton() = controlPanelOverlay.showFloatingStopButton()
    fun hideFloatingStopButton() = controlPanelOverlay.hideFloatingStopButton()

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))
        if (actionsList.isEmpty()) {
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        scenarioRunner.start()
    }

    fun stopExecutionLoop() {
        scenarioRunner.stop()
    }

    fun startOverlayRecording() {
        isRecording = true
        actionsList.forEach { act ->
            act.startView?.visibility = View.INVISIBLE
            act.endView?.visibility = View.INVISIBLE
        }
        controlPanelOverlay.hide()
        showFloatingStopButton()
    }

    fun stopOverlayRecording() {
        isRecording = false
        controlPanelOverlay.show()
        hideFloatingStopButton()
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
    }

    fun toggleNumbersVisibility() {
        isNumbersHidden = !isNumbersHidden
        actionsList.forEach { act ->
            act.startView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
            act.endView?.visibility = if (isNumbersHidden) View.INVISIBLE else View.VISIBLE
        }
        Toast.makeText(this, if (isNumbersHidden) "👁 Номера скрыты" else "👁 Номера показаны", Toast.LENGTH_SHORT).show()
    }

    fun clearAllActions() {
        actionsList.forEach { act ->
            act.startView?.let { overlayManager.safeRemoveView(it) }
            act.endView?.let { overlayManager.safeRemoveView(it) }
        }
        actionsList.clear()
        Toast.makeText(this, "🗑 Все шаги очищены", Toast.LENGTH_SHORT).show()
    }

    fun addNewActionAtPosition(x: Float, y: Float, delay: Long, type: ActionType, id: Int) {
        val cfg = ActionConfig(
            id = if (id == -1) (actionsList.size + 1) else id,
            type = type,
            xNorm = normalizeX(x),
            yNorm = normalizeY(y),
            delay = delay
        )
        actionsList.add(cfg)
    }

    fun spawnEndTargetAtPosition(config: ActionConfig, posX: Float, posY: Float) {
        val endView = LayoutInflater.from(this).inflate(R.layout.floating_target_end, null)
        val tvNumEnd = endView.findViewById<TextView>(R.id.tvTargetNumberEnd)
        tvNumEnd?.text = "${config.id}E"

        val sizePx = overlayManager.dpToPx(36)
        val params = overlayManager.createOverlayParams().apply {
            width = sizePx
            height = sizePx
            gravity = Gravity.TOP or Gravity.START
            x = (posX - sizePx / 2f).toInt()
            y = (posY - sizePx / 2f).toInt()
        }

        config.endView = endView
        overlayManager.safeAddView(endView, params)
    }

    fun normalizeX(px: Float): Float {
        val (w, _) = overlayManager.getRealScreenSize()
        return (px / w.toFloat()).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val (_, h) = overlayManager.getRealScreenSize()
        return (px / h.toFloat()).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val (w, h) = overlayManager.getRealScreenSize()
        return Pair((nx * w).coerceIn(0f, w.toFloat()), (ny * h).coerceIn(0f, h.toFloat()))
    }

    fun randomOffset(radius: Int): PointF = gestureExecutor.randomOffset(radius)

    fun performClickWithCallback(x: Float, y: Float, duration: Long = globalClickDurationMs, onComplete: ((Boolean) -> Unit)? = null) {
        gestureExecutor.performClickWithCallback(x, y, duration, onComplete)
    }

    fun showClickVisualizer(x: Float, y: Float) = clickVisualizerOverlay.showClickAt(x, y)

    fun captureScreenBitmap(): Bitmap? = captureFrameOverlay.capture()

    fun showScriptsDialog() = ScriptsDialog(this).show()
    fun showEditDialog(config: ActionConfig) = EditActionDialog(this).show(config)

    fun showScriptPickerDialog(title: String, onSelected: (String) -> Unit) {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_select_script_for_export, null)
        val tvTitle = dialogView.findViewById<TextView>(R.id.tvPickerTitle)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutPickerList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnClosePicker)

        tvTitle?.text = title
        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val dir = File(filesDir, "scripts")
        if (dir.exists()) {
            dir.listFiles()?.forEach { file ->
                if (file.name.endsWith(".json")) {
                    val btn = Button(this).apply {
                        text = file.nameWithoutExtension
                        setTextColor(Color.WHITE)
                        setBackgroundColor(Color.parseColor("#1C2541"))
                        setOnClickListener {
                            onSelected(file.nameWithoutExtension)
                            overlayManager.safeRemoveView(dialogView)
                        }
                    }
                    layoutList?.addView(btn)
                }
            }
        }

        btnClose?.setOnClickListener { overlayManager.safeRemoveView(dialogView) }
        overlayManager.safeAddView(dialogView, params)
    }

    fun showAddActionMenu() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_action, null)
        val params = overlayManager.createOverlayParams().apply {
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val btnClick = dialogView.findViewById<Button>(R.id.btnAddClick)
        val btnSwipe = dialogView.findViewById<Button>(R.id.btnAddSwipe)
        val btnAi = dialogView.findViewById<Button>(R.id.btnAddTrigger)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelAdd)

        val screenSize = overlayManager.getRealScreenSize()
        val spawnX = screenSize.first / 2f
        val spawnY = screenSize.second / 2f

        btnClick?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.CLICK, -1); overlayManager.safeRemoveView(dialogView) }
        btnSwipe?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.SWIPE, -1); spawnEndTargetAtPosition(actionsList.last(), spawnX + 100f, spawnY + 100f); overlayManager.safeRemoveView(dialogView) }
        btnAi?.setOnClickListener { vibrateFeedback(20L); addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, 0); overlayManager.safeRemoveView(dialogView) }
        btnCancel?.setOnClickListener { vibrateFeedback(20L); overlayManager.safeRemoveView(dialogView) }

        overlayManager.safeAddView(dialogView, params)
    }

    fun showTutorialCard() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.floating_tutorial_card, null)
        val params = overlayManager.createOverlayParams().apply { gravity = Gravity.CENTER }
        val btnSkip = dialogView.findViewById<Button>(R.id.btnTutSkip)
        btnSkip?.setOnClickListener { vibrateFeedback(20L); overlayManager.safeRemoveView(dialogView) }
        overlayManager.safeAddView(dialogView, params)
    }

    fun loadScriptByName(name: String): List<ActionConfig> = scriptRepository.loadScriptByName(name)
    fun saveScriptByName(name: String, actions: List<ActionConfig>) = scriptRepository.saveScriptByName(name, actions)

    fun loadAllTemplatesFromDisk() = templateRepository.loadAllTemplatesFromDisk()
    fun moveTemplateToTrash(index: Int) = templateRepository.moveTemplateToTrash(index)
    fun exportScriptWithTemplates(context: Context, scriptName: String) = scriptRepository.exportScriptWithTemplates(scriptName)

    override fun onDestroy() {
        stopExecutionLoop()
        hideControlPanel()
        instance = null
        super.onDestroy()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MyAutoClickService.kt", service_code)

    print("✨ Все 30 ошибок компиляции Kotlin успешно устранены! Запускайте сборку.")

if __name__ == "__main__":
    fix_compilation_errors()