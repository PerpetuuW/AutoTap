package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.model.ActionConfig
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class EditActionDialog(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.floating_edit_dialog

    private var currentAction: ActionConfig? = null
    private var actionIndex: Int = 0
    private var onApplyCallback: ((ActionConfig) -> Unit)? = null
    private var onDeleteCallback: (() -> Unit)? = null

    fun bindAction(
        action: ActionConfig,
        index: Int,
        onApply: ((ActionConfig) -> Unit)? = null,
        onDelete: (() -> Unit)? = null
    ) {
        this.currentAction = action
        this.actionIndex = index
        this.onApplyCallback = onApply
        this.onDeleteCallback = onDelete
        show()
        val v = rootView ?: return
        bind(v)
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)
        bind(view)
        return view
    }

    private fun bind(v: View) {
        val tvTitle = v.findViewById<TextView>(R.id.tvEditTitle)
        val etX = v.findViewById<EditText>(R.id.etEditX)
        val etY = v.findViewById<EditText>(R.id.etEditY)
        val etDelay = v.findViewById<EditText>(R.id.etEditDelayMs)
        val etComment = v.findViewById<EditText>(R.id.etEditComment)
        val btnApply = v.findViewById<Button>(R.id.btnEditApply)
        val btnDelete = v.findViewById<Button>(R.id.btnEditDelete)
        val btnClose = v.findViewById<Button>(R.id.btnEditClose)

        val action = currentAction ?: ActionConfig()
        tvTitle?.text = "Действие #${actionIndex + 1} (${action.type.name})"

        val metrics = context.resources.displayMetrics
        val currentXPx = (action.xNorm * metrics.widthPixels).toInt()
        val currentYPx = (action.yNorm * metrics.heightPixels).toInt()

        etX?.setText(currentXPx.toString())
        etY?.setText(currentYPx.toString())
        etDelay?.setText(action.delay.toString())

        btnApply?.setOnClickListener {
            val xPx = etX?.text?.toString()?.toIntOrNull() ?: currentXPx
            val yPx = etY?.text?.toString()?.toIntOrNull() ?: currentYPx
            val delayVal = etDelay?.text?.toString()?.toLongOrNull()?.coerceAtLeast(10L) ?: action.delay

            action.xNorm = (xPx.toFloat() / metrics.widthPixels).coerceIn(0f, 1f)
            action.yNorm = (yPx.toFloat() / metrics.heightPixels).coerceIn(0f, 1f)
            action.delay = delayVal

            onApplyCallback?.invoke(action)
            logDiagnostic("SCRIPT", "Шаг #${actionIndex + 1} обновлен ($xPx, $yPx px, delay=$delayVal ms)")
            hide()
        }

        btnDelete?.setOnClickListener {
            onDeleteCallback?.invoke()
            val list = MyAutoClickService.instance?.actionsList
            if (list != null && actionIndex in list.indices) {
                list.removeAt(actionIndex)
                logDiagnostic("SCRIPT", "Шаг #${actionIndex + 1} удален.")
            }
            hide()
        }

        btnClose?.setOnClickListener {
            hide()
        }
    }
}
