package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Bitmap
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.dpToPx
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import kotlin.math.sqrt

class MaskEditorDialog(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_mask_editor

    private var isResizing = false
    private var startWidth = 0
    private var startHeight = 0
    private var touchStartX = 0f
    private var touchStartY = 0f

    private var currentMaskBitmap: Bitmap? = null
    private var currentTemplateIndex: Int = 0

    override fun createView(): View {
        val inflater = android.view.LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        bindViews(view)
        return view
    }

    fun openForEditing(bitmap: Bitmap, templateIndex: Int) {
        this.currentMaskBitmap = bitmap
        this.currentTemplateIndex = templateIndex
        show()
        val v = rootView ?: return
        bindViews(v)
    }

    private fun bindViews(v: View) {
        val ivMask = v.findViewById<ImageView>(R.id.ivMaskPreview) ?: return
        val cropFrame = v.findViewById<FrameLayout>(R.id.maskCropFrame) ?: return
        val resizeHandle = v.findViewById<View>(R.id.handleResizeMask) ?: return

        currentMaskBitmap?.let { bmp ->
            ivMask.setImageBitmap(bmp)
        }

        v.findViewById<Button>(R.id.btnMaskSave)?.setOnClickListener {
            val bmp = currentMaskBitmap
            if (bmp != null) {
                val crop = cropMask(ivMask, cropFrame, bmp)
                if (crop != null) {
                    MyAutoClickService.instance?.templateRepository?.saveTemplate(currentTemplateIndex, crop)
                    logDiagnostic("AI_SCANNER", "Редактированная маска #$currentTemplateIndex сохранена.")
                }
            }
            hide()
        }

        v.findViewById<Button>(R.id.btnMaskCopy)?.setOnClickListener {
            val bmp = currentMaskBitmap
            val svc = MyAutoClickService.instance
            if (bmp != null && svc != null) {
                val nextIdx = svc.templateRepository.getNextFreeTemplateIndex()
                val crop = cropMask(ivMask, cropFrame, bmp)
                if (crop != null) {
                    svc.templateRepository.saveTemplate(nextIdx, crop)
                    logDiagnostic("AI_SCANNER", "Создана копия маски под слотом #$nextIdx.")
                }
            }
        }

        v.findViewById<Button>(R.id.btnMaskDelete)?.setOnClickListener {
            MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(currentTemplateIndex)
            hide()
        }

        v.findViewById<Button>(R.id.btnMaskClose)?.setOnClickListener {
            hide()
        }

        setupResize(resizeHandle, cropFrame)
    }

    private fun cropMask(iv: ImageView, frame: FrameLayout, maskBitmap: Bitmap): Bitmap? {
        val loc = IntArray(2)
        iv.getLocationOnScreen(loc)
        val ivX = loc[0]
        val ivY = loc[1]

        frame.getLocationOnScreen(loc)
        val fx = loc[0]
        val fy = loc[1]

        val x = (fx - ivX).coerceAtLeast(0)
        val y = (fy - ivY).coerceAtLeast(0)
        val w = frame.width.coerceAtMost(maskBitmap.width - x).coerceAtLeast(1)
        val h = frame.height.coerceAtMost(maskBitmap.height - y).coerceAtLeast(1)

        return try {
            Bitmap.createBitmap(maskBitmap, x, y, w, h)
        } catch (_: Exception) {
            null
        }
    }

    private fun setupResize(handle: View, frame: FrameLayout) {
        val slop = ViewConfiguration.get(context).scaledTouchSlop

        handle.setOnTouchListener { _, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    isResizing = false
                    startWidth = frame.width
                    startHeight = frame.height
                    touchStartX = event.rawX
                    touchStartY = event.rawY
                    false
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - touchStartX
                    val dy = event.rawY - touchStartY
                    val dist = sqrt(dx * dx + dy * dy)

                    if (!isResizing && dist > slop) {
                        isResizing = true
                    }

                    if (isResizing) {
                        val newW = (startWidth + dx).toInt().coerceAtLeast(context.dpToPx(40))
                        val newH = (startHeight + dy).toInt().coerceAtLeast(context.dpToPx(40))
                        frame.layoutParams.width = newW
                        frame.layoutParams.height = newH
                        frame.requestLayout()
                        true
                    } else false
                }
                MotionEvent.ACTION_UP,
                MotionEvent.ACTION_CANCEL -> {
                    isResizing = false
                    false
                }
                else -> false
            }
        }
    }
}
