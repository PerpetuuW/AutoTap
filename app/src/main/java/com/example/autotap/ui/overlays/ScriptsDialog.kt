package com.example.autotap.ui.overlays

import com.example.autotap.*

import android.content.res.ColorStateList
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import java.io.File

class ScriptsDialog(service: MyAutoClickService) :
    OverlayBase(service, R.layout.dialog_scripts, OverlayLayer.PANEL, OverlayPriority.MEDIUM) {

    private var etScriptName: EditText? = null
    private var btnSaveScriptAction: Button? = null
    private var layoutScriptsList: LinearLayout? = null
    private var btnCloseScripts: Button? = null
    private var btnCloseScriptsHeader: View? = null
    private var etLoopCount: EditText? = null
    private var btnInfinite: Button? = null
    private var btnSelectRelay: Button? = null

    override fun onViewInflated(view: View) {
        etScriptName = view.findViewById(R.id.etScriptName)
        btnSaveScriptAction = view.findViewById(R.id.btnSaveScriptAction)
        layoutScriptsList = view.findViewById(R.id.layoutScriptsList)
        btnCloseScripts = view.findViewById(R.id.btnCloseScripts)
        btnCloseScriptsHeader = view.findViewById(R.id.btnCloseScriptsHeader)
        etLoopCount = view.findViewById(R.id.etScriptLoopCount)
        btnInfinite = view.findViewById(R.id.btnToggleScriptInfinite)
        btnSelectRelay = view.findViewById(R.id.btnSelectScriptRelay)

        bindUi()
    }

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
            gravity = android.view.Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }
    }

    private fun bindUi() {
        etLoopCount?.setText(service.globalScriptLoopCount.toString())

        fun updateHeaderUi() {
            btnInfinite?.text = if (service.isGlobalScriptInfinite) "Бесконечный цикл всего сценария: [ ВКЛ ]" else "Бесконечный цикл всего сценария: [ НЕТ ]"
            btnInfinite?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (service.isGlobalScriptInfinite) R.color.accent_blue else R.color.bg_dark_blue))

            btnSelectRelay?.text = if (service.globalRelayNextScript.isNotEmpty()) "🔗 Эстафета: [ ${service.globalRelayNextScript} 📁 ]" else "🔗 Эстафета: [ Выбрать следующий сценарий 📁 ]"
            btnSelectRelay?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (service.globalRelayNextScript.isNotEmpty()) R.color.accent_blue else R.color.bg_dark_blue))
        }

        fun refreshList() {
            layoutScriptsList?.removeAllViews()
            val dir = File(service.filesDir, "scripts")
            if (dir.exists()) {
                dir.listFiles()?.forEach { file ->
                    if (file.name.endsWith(".json")) {
                        val item = android.view.LayoutInflater.from(service).inflate(R.layout.item_script, null)
                        val tvName = item.findViewById<TextView>(R.id.tvScriptName)
                        val btnExport = item.findViewById<Button>(R.id.btnExportScriptFile)
                        val btnCopy = item.findViewById<Button>(R.id.btnCopyScriptFile)
                        val btnDelete = item.findViewById<Button>(R.id.btnDeleteScriptFile)

                        val actions = service.loadScriptByName(file.nameWithoutExtension)
                        tvName?.text = "${file.nameWithoutExtension} (${actions.size} шагов)"

                        tvName?.setOnClickListener {
                            service.loadScriptByName(file.nameWithoutExtension)
                            hide()
                        }

                        btnExport?.setOnClickListener { service.exportScriptWithTemplates(service, file.nameWithoutExtension) }

                        btnCopy?.setOnClickListener {
                            try {
                                val newName = "${file.nameWithoutExtension}_copy"
                                val newFile = File(dir, "$newName.json")
                                file.copyTo(newFile, overwrite = true)
                                refreshList()
                                Toast.makeText(service, "📋 Скопировано: $newName", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) { MyAutoClickService.logError(service, e) }
                        }

                        btnDelete?.setOnClickListener {
                            file.delete()
                            refreshList()
                        }

                        layoutScriptsList?.addView(item)
                    }
                }
            }
        }

        btnInfinite?.setOnClickListener { service.vibrateFeedback(20L); service.isGlobalScriptInfinite = !service.isGlobalScriptInfinite; updateHeaderUi() }
        btnSelectRelay?.setOnClickListener { service.vibrateFeedback(20L); service.showScriptPickerDialog("Выберите следующий сценарий") { sc -> service.globalRelayNextScript = sc; updateHeaderUi() } }

        btnSaveScriptAction?.setOnClickListener {
            val name = etScriptName?.text?.toString()?.trim() ?: ""
            if (name.isNotEmpty()) {
                service.globalScriptLoopCount = etLoopCount?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
                service.saveScriptByName(name, service.actionsList)
                refreshList()
                etScriptName?.setText("")
            }
        }

        btnCloseScriptsHeader?.setOnClickListener { service.vibrateFeedback(20L); hide() }
        btnCloseScripts?.setOnClickListener { service.vibrateFeedback(20L); hide() }

        updateHeaderUi()
        refreshList()
    }
}
