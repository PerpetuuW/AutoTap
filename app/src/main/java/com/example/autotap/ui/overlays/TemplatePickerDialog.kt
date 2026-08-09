package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class TemplatePickerDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_template_picker

    private var templatesContainer: LinearLayout? = null
    private val selectedIndices = mutableSetOf<Int>()
    private var onApplyCallback: ((List<Int>) -> Unit)? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
    }

    fun showPicker(currentIndices: List<Int>, callback: (List<Int>) -> Unit) {
        this.selectedIndices.clear()
        this.selectedIndices.addAll(currentIndices)
        this.onApplyCallback = callback
        show()
        populateGrid()
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        templatesContainer = view.findViewByNames("layoutTemplatesGrid") as? LinearLayout

        view.bindClickByNames("btnSelectAllPicker") {
            setAllChecked(true)
        }

        view.bindClickByNames("btnUnselectAllPicker") {
            setAllChecked(false)
        }

        view.bindClickByNames("btnApplyPicker") {
            val sorted = selectedIndices.sorted()
            logDiagnostic("AI_SCANNER", "Выбраны маски для мультипоиска: $sorted")
            onApplyCallback?.invoke(sorted)
            hide()
        }

        view.bindClickByNames("btnCancelPicker") {
            hide()
        }

        return view
    }

    private fun populateGrid() {
        val container = templatesContainer ?: return
        container.removeAllViews()

        val files = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") }
            ?.sortedBy { file ->
                file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: 0
            } ?: emptyList()

        if (files.isEmpty()) {
            val tv = TextView(context).apply {
                text = "Шаблонов пока нет. Вырежьте их прицелом 📷"
                setTextColor(Color.GRAY)
                gravity = Gravity.CENTER
                setPadding(16, 32, 16, 32)
            }
            container.addView(tv)
            return
        }

        for (file in files) {
            val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
            val row = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setBackgroundResource(R.drawable.drag_handle_bg)
                setPadding(12, 10, 12, 10)
                val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
                lp.setMargins(0, 0, 0, 8)
                layoutParams = lp
            }

            val cb = CheckBox(context).apply {
                isChecked = selectedIndices.contains(index)
                setOnCheckedChangeListener { _, isChecked ->
                    if (isChecked) selectedIndices.add(index) else selectedIndices.remove(index)
                }
            }

            val iv = ImageView(context).apply {
                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                if (bitmap != null) setImageBitmap(bitmap)
                layoutParams = LinearLayout.LayoutParams(60.dpToPx(context), 60.dpToPx(context)).apply {
                    setMargins(12, 0, 16, 0)
                }
                scaleType = ImageView.ScaleType.FIT_CENTER
                setBackgroundResource(R.drawable.border_capture_square)
            }

            val tv = TextView(context).apply {
                text = "ИИ-Маска #$index
Размер: ${file.length() / 1024} КБ"
                setTextColor(Color.WHITE)
                textSize = 13f
            }

            row.addView(cb)
            row.addView(iv)
            row.addView(tv)
            container.addView(row)
        }
    }

    private fun setAllChecked(checked: Boolean) {
        val container = templatesContainer ?: return
        selectedIndices.clear()

        val files = context.filesDir.listFiles { _, name -> name.startsWith("template_") && name.endsWith(".png") } ?: emptyArray()
        if (checked) {
            for (file in files) {
                val index = file.name.removePrefix("template_").removeSuffix(".png").toIntOrNull() ?: continue
                selectedIndices.add(index)
            }
        }

        for (i in 0 until container.childCount) {
            val row = container.getChildAt(i) as? LinearLayout ?: continue
            val cb = row.getChildAt(0) as? CheckBox ?: continue
            cb.isChecked = checked
        }
    }

    private fun Int.dpToPx(context: Context): Int {
        return (this * context.resources.displayMetrics.density).toInt()
    }
}
