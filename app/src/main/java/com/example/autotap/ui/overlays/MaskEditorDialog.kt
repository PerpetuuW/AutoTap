package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.BitmapFactory
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
import java.io.File

class MaskEditorDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_mask_editor

    private var targetIndex = 0
    private var ivPreview: ImageView? = null
    private var tvTitle: TextView? = null

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    fun setTargetTemplateIndex(index: Int) {
        this.targetIndex = index
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        ivPreview = view.findViewByNames("ivMaskPreview") as? ImageView
        tvTitle = view.findViewByNames("tvMaskEditorTitle") as? TextView

        tvTitle?.text = "Редактор маски #$targetIndex"

        val file = File(context.filesDir, "template_$targetIndex.png")
        if (file.exists()) {
            val bmp = BitmapFactory.decodeFile(file.absolutePath)
            ivPreview?.setImageBitmap(bmp)
        }

        view.bindClickByNames("btnMaskSave", "btnSaveMaskEdits") {
            MyAutoClickService.instance?.templateRepository?.recalibrateTemplate(targetIndex)
            logDiagnostic("AI_SCANNER", "Маска #$targetIndex успешно перекалибрована.")
            hide()
        }

        view.bindClickByNames("btnMaskDelete") {
            MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(targetIndex)
            overlayManager.templatesManagerDialog.refreshTemplatesList()
            hide()
        }

        view.bindClickByNames("btnMaskClose", "btnCancelMaskEdits", "btnCloseMaskEditor") {
            hide()
        }

        return view
    }
}
