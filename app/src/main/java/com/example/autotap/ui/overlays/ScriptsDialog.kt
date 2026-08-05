package com.example.autotap.ui.overlays
import com.example.autotap.*

import android.content.res.ColorStateList
import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class ScriptsDialog(private val service: MyAutoClickService) {

    fun show() {
        val dialogView = LayoutInflater.from(service).inflate(R.layout.dialog_scripts, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
            dimAmount = 0.5f
        }

        val etScriptName = dialogView.findViewById<EditText>(R.id.etScriptName)
        val btnSaveScriptAction = dialogView.findViewById<Button>(R.id.btnSaveScriptAction)
        val layoutScriptsList = dialogView.findViewById<LinearLayout>(R.id.layoutScriptsList)
        val btnCloseScripts = dialogView.findViewById<Button>(R.id.btnCloseScripts)

        val etLoopCount = dialogView.findViewById<EditText>(R.id.etScriptLoopCount)
        val btnInfinite = dialogView.findViewById<Button>(R.id.btnToggleScriptInfinite)
        val btnSelectRelay = dialogView.findViewById<Button>(R.id.btnSelectScriptRelay)

        etLoopCount?.setText(service.globalScriptLoopCount.toString())

        fun updateScriptHeaderUI() {
            btnInfinite?.text = if (service.isGlobalScriptInfinite) "Бесконечный цикл всего сценария: [ ВКЛ ]" else "Бесконечный цикл всего сценария: [ НЕТ ]"
            btnInfinite?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (service.isGlobalScriptInfinite) R.color.accent_blue else R.color.bg_dark_blue))

            btnSelectRelay?.text = if (service.globalRelayNextScript.isNotEmpty()) "🔗 Эстафета: [ ${service.globalRelayNextScript} 📁 ]" else "🔗 Эстафета: [ Выбрать следующий сценарий 📁 ]"
            btnSelectRelay?.backgroundTintList = ColorStateList.valueOf(service.getColor(if (service.globalRelayNextScript.isNotEmpty()) R.color.accent_blue else R.color.bg_dark_blue))
        }
        updateScriptHeaderUI()

        btnInfinite?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.isGlobalScriptInfinite = !service.isGlobalScriptInfinite
            updateScriptHeaderUI()
        }

        btnSelectRelay?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showScriptPickerDialog("Выберите следующий сценарий для эстафеты") { scName ->
                service.globalRelayNextScript = scName
                updateScriptHeaderUI()
            }
        }

        fun refreshScriptsList() {
            layoutScriptsList?.removeAllViews()
            val dir = File(service.filesDir, "scripts")
            if (dir.exists()) {
                val files = dir.listFiles()?.filter { it.name.endsWith(".json") } ?: emptyList()
            for (file in files) { file ->
                    if (file.name.endsWith(".json")) {
                        val itemView = LayoutInflater.from(service).inflate(R.layout.item_script, null)
                        val tvName = itemView.findViewById<TextView>(R.id.tvScriptName)
                        val btnExport = itemView.findViewById<Button>(R.id.btnExportScriptFile)
                        val btnDelete = itemView.findViewById<Button>(R.id.btnDeleteScriptFile)

                        tvName?.text = file.nameWithoutExtension
                        tvName?.setOnClickListener {
                            service.loadScriptByName(file.nameWithoutExtension)
                            service.overlayManager.safeRemoveView(dialogView)
                        }

                        btnExport?.setOnClickListener {
                            service.exportScriptWithTemplates(service, file.nameWithoutExtension)
                        }

                        btnDelete?.setOnClickListener {
                            file.delete()
                            refreshScriptsList()
                        }
                        layoutScriptsList?.addView(itemView)
                    }
                }
            }
        }

        refreshScriptsList()

        btnSaveScriptAction?.setOnClickListener {
            val name = etScriptName?.text?.toString()?.trim() ?: ""
            if (name.isNotEmpty()) {
                service.globalScriptLoopCount = etLoopCount?.text?.toString()?.toIntOrNull()?.coerceAtLeast(1) ?: 1
                service.scriptRepository.saveScriptByName(name, service.actionsList)
                refreshScriptsList()
                etScriptName?.setText("")
            }
        }

        btnCloseScripts?.setOnClickListener { service.overlayManager.safeRemoveView(dialogView) }
        service.overlayManager.safeAddView(dialogView, params)
    }
}
