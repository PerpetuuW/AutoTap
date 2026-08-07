package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.BitmapFactory
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageView
import android.widget.LinearLayout
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

class TemplatesManagerDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var templatesListLayout: LinearLayout? = null

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
        val view = inflater.inflate(R.layout.dialog_templates_manager, null)

        templatesListLayout = view.findViewByNames("layoutTemplatesList") as? LinearLayout

        view.bindClickByNames("btnOpenTrashBin") {
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.templateRepository.restoreTemplateFromTrash(0)
                refreshTemplatesList()
                logDiagnostic("UI", "Восстановление масок из корзины.")
            }
        }

        view.bindClickByNames("btnCloseTemplatesManager") {
            hide()
        }

        refreshTemplatesList()
        return view
    }

    fun refreshTemplatesList() {
        val container = templatesListLayout ?: return
        container.removeAllViews()

        val filesDir = context.filesDir
        val templateFiles = filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") }
            ?.sortedBy { file ->
                file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: 0
            } ?: emptyList()

        if (templateFiles.isEmpty()) {
            val emptyTv = TextView(context).apply {
                text = "Шаблонов масок пока нет.\nСоздайте их через Прицел 📷"
                setTextColor(android.graphics.Color.GRAY)
                gravity = Gravity.CENTER
                setPadding(16, 32, 16, 32)
            }
            container.addView(emptyTv)
            return
        }

        val inflater = LayoutInflater.from(context)
        for (file in templateFiles) {
            val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
            val itemView = try {
                inflater.inflate(R.layout.item_template, container, false)
            } catch (e: Exception) { continue }

            val tvName = itemView.findViewByNames("tvTemplateName") as? TextView
            val ivPreview = itemView.findViewByNames("ivTemplatePreview") as? ImageView

            tvName?.text = "Маска #$index (${file.length() / 1024} КБ)"

            val bitmap = BitmapFactory.decodeFile(file.absolutePath)
            if (bitmap != null) {
                ivPreview?.setImageBitmap(bitmap)
            }

            itemView.bindClickByNames("btnEditTemplateMask") {
                overlayManager.maskEditorDialog.setTargetTemplateIndex(index)
                overlayManager.maskEditorDialog.show()
            }

            itemView.bindClickByNames("btnDeleteTemplateFile") {
                MyAutoClickService.instance?.templateRepository?.moveTemplateToTrash(index)
                refreshTemplatesList()
            }

            container.addView(itemView)
        }
    }
}
