package com.example.autotap.ui.overlays

import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.data.ScriptMetadata
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ScriptsDialog(
    context: Context,
    overlayManager: OverlayManager
) : OverlayBase(context, OverlayLayer.DIALOG_LAYER, OverlayPriority.CRITICAL) {

    override val layoutResId: Int = R.layout.dialog_scripts

    private var isInfinite = false
    private var relayScript = ""

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(layoutResId, null)

        val etName = view.findViewById<EditText>(R.id.etScriptName)
        val etLoop = view.findViewById<EditText>(R.id.etScriptLoopCount)
        val btnSave = view.findViewById<Button>(R.id.btnSaveScriptAction)
        val btnInfinite = view.findViewById<Button>(R.id.btnToggleScriptInfinite)
        val btnRelay = view.findViewById<Button>(R.id.btnSelectScriptRelay)
        val btnClose = view.findViewById<Button>(R.id.btnCloseScripts)
        val listLayout = view.findViewById<LinearLayout>(R.id.layoutScriptsList)

        fun updateHeader() {
            btnInfinite?.text = if (isInfinite) "♾ Бесконечно: [ ВКЛ ]" else "♾ Бесконечно: [ ВЫКЛ ]"
            btnInfinite?.setTextColor(if (isInfinite) Color.parseColor("#00E676") else Color.WHITE)
            btnRelay?.text = if (relayScript.isNotEmpty()) "🔗 Эстафета: $relayScript" else "🔗 Эстафета"
        }

        updateHeader()

        btnInfinite?.setOnClickListener {
            isInfinite = !isInfinite
            updateHeader()
        }

        btnRelay?.setOnClickListener {
            logDiagnostic("SCRIPT", "Выбор эстафетного скрипта.")
        }

        btnSave?.setOnClickListener {
            val name = etName?.text?.toString()?.trim()?.ifBlank {
                "script_${SimpleDateFormat("MMdd_HHmm", Locale.US).format(Date())}"
            } ?: "script_${System.currentTimeMillis() % 10000}"

            val loopCount = etLoop?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
            val svc = MyAutoClickService.instance
            if (svc != null) {
                val metadata = ScriptMetadata(
                    name = name,
                    stepCount = svc.actionsList.size,
                    loopCount = loopCount,
                    isInfinite = isInfinite,
                    relayScript = relayScript
                )
                svc.scriptRepository.saveScript(name, svc.actionsList, metadata)
                etName?.setText("")
                refreshList(listLayout)
            }
        }

        btnClose?.setOnClickListener {
            hide()
        }

        if (listLayout != null) {
            refreshList(listLayout)
        }

        return view
    }

    private fun refreshList(listLayout: LinearLayout) {
        listLayout.removeAllViews()

        val filesDir = context.filesDir
        filesDir?.listFiles()?.forEach { file ->
            if (!file.name.endsWith(".json")) return@forEach

            val item = LayoutInflater.from(context).inflate(R.layout.item_script, null)
            val tvName = item.findViewById<TextView>(R.id.tvScriptName)
            val btnExport = item.findViewById<Button>(R.id.btnExportScriptFile)
            val btnDelete = item.findViewById<Button>(R.id.btnDeleteScriptFile)

            val scriptName = file.nameWithoutExtension
            tvName?.text = scriptName

            tvName?.setOnClickListener {
                MyAutoClickService.instance?.loadScriptByName(scriptName)
                hide()
            }

            btnExport?.setOnClickListener {
                logDiagnostic("SCRIPT", "Экспорт файла сценария $scriptName")
            }

            btnDelete?.setOnClickListener {
                file.delete()
                refreshList(listLayout)
            }

            listLayout.addView(item)
        }
    }
}
