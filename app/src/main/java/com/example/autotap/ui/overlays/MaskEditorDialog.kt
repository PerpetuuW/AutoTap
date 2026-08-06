package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageView
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import com.example.autotap.vibrateFeedback

class MaskEditorDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var cropWidth = 100
    private var cropHeight = 100
    private var isSquareShape = true
    private var selectedTemplateIdx = 0

    private var ivFullScreenshotView: ImageView? = null
    private var ivMaskPreviewView: ImageView? = null

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_mask_editor, null)

        ivFullScreenshotView = view.findViewByNames("ivEditorFullScreenshot") as? ImageView
        ivMaskPreviewView = view.findViewByNames("ivEditorMaskPreview") as? ImageView

        view.bindClickByNames("btnCropWidthPlus") {
            cropWidth += 20
            updateCropDisplay(view)
        }

        view.bindClickByNames("btnCropWidthMinus") {
            cropWidth = (cropWidth - 20).coerceAtLeast(20)
            updateCropDisplay(view)
        }

        view.bindClickByNames("btnCropHeightPlus") {
            cropHeight += 20
            updateCropDisplay(view)
        }

        view.bindClickByNames("btnToggleMaskShape") {
            isSquareShape = !isSquareShape
            updateCropDisplay(view)
        }

        view.bindClickByNames("btnTemplateSearchArea") {
            overlayManager.searchAreaOverlay.show()
        }

        view.bindClickByNames("btnCopyMaskEdits") {
            logDiagnostic("AI_SCANNER", "Создана копия маски #$selectedTemplateIdx.")
            context.vibrateFeedback()
        }

        view.bindClickByNames("btnSaveMaskEdits") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.templateRepository.recalibrateTemplate(selectedTemplateIdx)
                context.vibrateFeedback()
                logDiagnostic("AI_SCANNER", "Маска #$selectedTemplateIdx отредактирована (${cropWidth}x${cropHeight}px).")
            }
            hide()
        }

        view.bindClickByNames("btnCancelMaskEdits", "btnCloseMaskEditor") {
            hide()
        }

        updateCropDisplay(view)
        return view
    }

    fun setSelectedTemplateIndex(idx: Int) {
        selectedTemplateIdx = idx
    }

    private fun updateCropDisplay(root: View) {
        val tv = root.findViewByNames("tvCropSizeDisplay") as? TextView
        val shapeStr = if (isSquareShape) "🔲 Прямоугольник" else "🔘 Круг"
        tv?.text = "Маска #$selectedTemplateIdx | $shapeStr ${cropWidth}x${cropHeight} px"
    }
}
