package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
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

class ScriptsDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_scripts

    private var etScriptName: EditText? = null
    private var etScriptLoopCount: EditText? = null
    private var scriptsListContainer: LinearLayout? = null

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND
        dimAmount = 0.6f
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        etScriptName = view.findViewByNames("etScriptName") as? EditText
        etScriptLoopCount = view.findViewByNames("etScriptLoopCount") as? EditText
        scriptsListContainer = view.findViewByNames("layoutScriptsList") as? LinearLayout

        view.bindClickByNames("btnSaveScriptAction") {
            val name = etScriptName?.text?.toString()?.takeIf { it.isNotBlank() } ?: "script_1"
            val loops = etScriptLoopCount?.text?.toString()?.toIntOrNull() ?: 1
            val svc = MyAutoClickService.instance
            if (svc != null) {
                svc.saveScriptByName(name, svc.actionsList)
                logDiagnostic("SCRIPT", "Сценарий '$name' успешно сохранен.")
                Toast.makeText(context, "Сценарий '$name' сохранен!", Toast.LENGTH_SHORT).show()
                refreshScriptsList()
            }
        }

        view.bindClickByNames("btnCloseScripts", "btnCloseScriptsHeader") {
            hide()
        }

        refreshScriptsList()
        return view
    }

    override fun show() {
        super.show()
        setFocusable(true)
        refreshScriptsList()
    }

    private fun refreshScriptsList() {
        val container = scriptsListContainer ?: return
        container.removeAllViews()

        val jsonFiles = context.filesDir.listFiles { _, name -> name.endsWith(".json") && !name.contains("meta") }
            ?.sortedByDescending { it.lastModified() } ?: emptyList()

        if (jsonFiles.isEmpty()) {
            val emptyTv = TextView(context).apply {
                text = "Сохраненных сценариев пока нет."
                setTextColor(Color.GRAY)
                gravity = Gravity.CENTER
                setPadding(16, 32, 16, 32)
            }
            container.addView(emptyTv)
            return
        }

        for (file in jsonFiles) {
            val scriptName = file.nameWithoutExtension
            val row = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setBackgroundResource(R.drawable.drag_handle_bg)
                setPadding(12, 10, 12, 10)
                val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
                lp.setMargins(0, 0, 0, 8)
                layoutParams = lp
            }

            val tv = TextView(context).apply {
                text = "$scriptName\n(${file.length() / 1024} КБ)"
                setTextColor(Color.WHITE)
                textSize = 13f
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f)
            }

            val btnLoad = Button(context).apply {
                text = "▶️ Загрузить"
                textSize = 10f
                setBackgroundColor(Color.parseColor("#1F6FEB"))
                setTextColor(Color.WHITE)
                setOnClickListener {
                    val svc = MyAutoClickService.instance
                    if (svc != null && svc.loadScriptByName(scriptName)) {
                        overlayManager.updateTargetMarkers()
                        Toast.makeText(context, "Загружен сценарий '$scriptName'", Toast.LENGTH_SHORT).show()
                        hide()
                    }
                }
            }

            val btnDel = Button(context).apply {
                text = "🗑"
                textSize = 10f
                setBackgroundColor(Color.parseColor("#2A1215"))
                setTextColor(Color.parseColor("#FF5B5B"))
                setOnClickListener {
                    file.delete()
                    refreshScriptsList()
                }
            }

            row.addView(tv)
            row.addView(btnLoad)
            row.addView(View(context), LinearLayout.LayoutParams(6, 1))
            row.addView(btnDel)
            container.addView(row)
        }
    }
}
