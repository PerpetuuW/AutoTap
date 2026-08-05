package com.example.autotap.ui.overlays

import com.example.autotap.*

import android.graphics.Bitmap
import android.graphics.Rect
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.TemplateMatcher
import com.example.autotap.data.TemplateMetadata
import com.example.autotap.engine.MaskCalibrator
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import java.io.File
import java.io.FileOutputStream

class CaptureFrameOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_capture_frame, OverlayLayer.CAPTURE, OverlayPriority.HIGH) {

    private var captureSquare: View? = null
    private var layoutTopBar: View? = null
    private var layoutBottomBar: View? = null
    private var handleMove: View? = null
    private var handleResize: View? = null
    private var btnDoCapture: ImageButton? = null
    private var btnSearchArea: Button? = null
    private var btnToggleShape: Button? = null
    private var btnCancel: ImageButton? = null

    private var frameW = 0
    private var frameH = 0
    private var frameX = 0
    private var frameY = 0
    private var isCircleShape = true

    override fun onViewInflated(view: View) {
        captureSquare = view.findViewById(R.id.captureSquare)
        layoutTopBar = view.findViewById(R.id.layoutTopBar)
        layoutBottomBar = view.findViewById(R.id.layoutBottomBar)
        handleMove = view.findViewById(R.id.handleMoveFrame)
        handleResize = view.findViewById(R.id.handleResize)
        btnDoCapture = view.findViewById(R.id.btnDoCapture)
        btnSearchArea = view.findViewById(R.id.btnCaptureSearchArea)
        btnToggleShape = view.findViewById(R.id.btnToggleCaptureShape)
        btnCancel = view.findViewById(R.id.btnCancelCapture)

        val (screenW, screenH) = service.overlayManager.getRealScreenSize()
        frameW = service.dpToPx(140)
        frameH = service.dpToPx(140)
        frameX = (screenW - frameW) / 2
        frameY = (screenH - frameH) / 2

        bindInteractions()

        view.post {
            updatePositions()
        }
    }

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }
    }

    private fun updatePositions() {
        val (screenW, screenH) = service.overlayManager.getRealScreenSize()

        val minSize = service.dpToPx(36)
        frameW = frameW.coerceIn(minSize, screenW)
        frameH = frameH.coerceIn(minSize, screenH)
        frameX = frameX.coerceIn(0, (screenW - frameW).coerceAtLeast(0))
        frameY = frameY.coerceIn(0, (screenH - frameH).coerceAtLeast(0))

        // 1. Прицел captureSquare
        captureSquare?.let { square ->
            val lp = square.layoutParams as? FrameLayout.LayoutParams
                ?: FrameLayout.LayoutParams(frameW, frameH)
            lp.width = frameW
            lp.height = frameH
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = frameX
            lp.topMargin = frameY
            square.layoutParams = lp
            square.requestLayout()
        }

        val topBarW = if (layoutTopBar?.width ?: 0 > 0) layoutTopBar!!.width else service.dpToPx(170)
        val topBarH = if (layoutTopBar?.height ?: 0 > 0) layoutTopBar!!.height else service.dpToPx(46)
        val botBarW = if (layoutBottomBar?.width ?: 0 > 0) layoutBottomBar!!.width else service.dpToPx(90)
        val botBarH = if (layoutBottomBar?.height ?: 0 > 0) layoutBottomBar!!.height else service.dpToPx(44)

        // 2. Верхняя панель кнопок layoutTopBar (Размещается НАД прицелом)
        layoutTopBar?.let { topBar ->
            val lp = topBar.layoutParams as? FrameLayout.LayoutParams
                ?: FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT)
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = (frameX + (frameW - topBarW) / 2).coerceIn(service.dpToPx(4), (screenW - topBarW - service.dpToPx(4)).coerceAtLeast(service.dpToPx(4)))

            lp.topMargin = if (frameY >= topBarH + service.dpToPx(8)) {
                frameY - topBarH - service.dpToPx(6)
            } else {
                frameY + frameH + service.dpToPx(6)
            }
            topBar.layoutParams = lp
            topBar.requestLayout()
        }

        // 3. Нижняя панель ручек layoutBottomBar (Размещается ПОД прицелом)
        layoutBottomBar?.let { botBar ->
            val lp = botBar.layoutParams as? FrameLayout.LayoutParams
                ?: FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT)
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = (frameX + (frameW - botBarW) / 2).coerceIn(service.dpToPx(4), (screenW - botBarW - service.dpToPx(4)).coerceAtLeast(service.dpToPx(4)))

            lp.topMargin = if (frameY >= topBarH + service.dpToPx(8)) {
                frameY + frameH + service.dpToPx(6)
            } else {
                frameY + frameH + topBarH + service.dpToPx(12)
            }
            botBar.layoutParams = lp
            botBar.requestLayout()
        }
    }

    private fun bindInteractions() {
        var initFrameX = 0; var initFrameY = 0
        var touchX = 0f; var touchY = 0f

        val dragFrameListener = object : View.OnTouchListener {
            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initFrameX = frameX
                        initFrameY = frameY
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        frameX = initFrameX + (event.rawX - touchX).toInt()
                        frameY = initFrameY + (event.rawY - touchY).toInt()
                        updatePositions()
                        return true
                    }
                }
                return false
            }
        }

        // Перетаскивать можно как за ручку ✥, так и за сам прицел captureSquare
        handleMove?.setOnTouchListener(dragFrameListener)
        captureSquare?.setOnTouchListener(dragFrameListener)

        var initW = 0; var initH = 0
        handleResize?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initW = frameW
                    initH = frameH
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    frameW = initW + (event.rawX - touchX).toInt()
                    frameH = initH + (event.rawY - touchY).toInt()
                    updatePositions()
                    true
                }
                else -> false
            }
        }

        btnToggleShape?.setOnClickListener {
            service.vibrateFeedback(20L)
            isCircleShape = !isCircleShape
            btnToggleShape?.text = if (isCircleShape) "🔘" else "🔲"
            captureSquare?.setBackgroundResource(
                if (isCircleShape) R.drawable.border_capture else R.drawable.border_capture_square
            )
        }

        btnSearchArea?.setOnClickListener {
            service.vibrateFeedback(20L)
            Toast.makeText(service, "📐 Полноэкранная зона поиска задана", Toast.LENGTH_SHORT).show()
        }

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(50L)
            val cropX = frameX.coerceAtLeast(0)
            val cropY = frameY.coerceAtLeast(0)
            val cropW = frameW
            val cropH = frameH

            hide()

            val screenshot = capture()
            if (screenshot != null) {
                val realMetrics = service.resources.displayMetrics
                val scaleX = screenshot.width.toFloat() / realMetrics.widthPixels.toFloat()
                val scaleY = screenshot.height.toFloat() / realMetrics.heightPixels.toFloat()

                val safeX = (cropX * scaleX).toInt().coerceIn(0, screenshot.width - 1)
                val safeY = (cropY * scaleY).toInt().coerceIn(0, screenshot.height - 1)
                val safeW = (cropW * scaleX).toInt().coerceIn(10, (screenshot.width - safeX).coerceAtLeast(10))
                val safeH = (cropH * scaleY).toInt().coerceIn(10, (screenshot.height - safeY).coerceAtLeast(10))

                val cropped = Bitmap.createBitmap(screenshot, safeX, safeY, safeW, safeH)
                val adaptedMask = MaskCalibrator.adaptMask(cropped)
                val smartMask = TemplateMatcher.generateSmartMask(adaptedMask, isCircleShape)

                val ts = System.currentTimeMillis()
                val tDir = File(service.filesDir, "templates/default").apply { mkdirs() }
                val maskFile = File(tDir, "mask_$ts.png")
                val fullFile = File(tDir, "full_$ts.png")

                FileOutputStream(maskFile).use { out -> smartMask.compress(Bitmap.CompressFormat.PNG, 100, out) }
                FileOutputStream(fullFile).use { out -> screenshot.compress(Bitmap.CompressFormat.PNG, 100, out) }

                val metadata = TemplateMetadata(
                    width = safeW,
                    height = safeH,
                    dpi = realMetrics.densityDpi,
                    scale = scaleX,
                    boundingBox = Rect(safeX, safeY, safeX + safeW, safeY + safeH),
                    isCircleShape = isCircleShape,
                    timestamp = ts
                )

                FileOutputStream(service.templateRepository.getTemplateMetadataFile(maskFile.absolutePath)).use { out ->
                    out.write(metadata.toJson().toString().toByteArray(Charsets.UTF_8))
                }

                service.loadAllTemplatesFromDisk()
                val newIndex = service.globalTemplatesNames.indexOf(maskFile.absolutePath)
                val spawnX = frameX + frameW / 2f
                val spawnY = frameY + frameH / 2f

                service.addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, newIndex)
                Toast.makeText(service, "🎉 ИИ-Шаблон успешно создан!", Toast.LENGTH_SHORT).show()

                val createdConfig = service.actionsList.last()
                service.aiScannerEngine.startTemplateCalibration(createdConfig)
            }
        }

        btnCancel?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }
    }

    fun startRecording() {
        show()
        service.isRecording = true
    }

    fun capture(): Bitmap? {
        return try {
            val (w, h) = service.overlayManager.getRealScreenSize()
            Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
