package com.example.autotap

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.StrictMode
import android.provider.Settings
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import androidx.core.content.edit
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.HashSet
import java.util.Locale
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream
import org.json.JSONArray
import org.json.JSONObject

@Suppress("SpellCheckingInspection", "DEPRECATION", "ClickableViewAccessibility")
class MainActivity : AppCompatActivity() {

    private var hasAutoShownPermissions = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            MyAutoClickService.logError(applicationContext, throwable)
            defaultHandler?.uncaughtException(thread, throwable)
        }

        val builder = StrictMode.VmPolicy.Builder()
        StrictMode.setVmPolicy(builder.build())

        val tvVersion = findViewById<TextView>(R.id.tvVersion)
        tvVersion?.text = "v28.11.0 PRO"

        val btnAppDetails = findViewById<Button>(R.id.btnAppDetails)
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)
        val btnExport = findViewById<Button>(R.id.btnExport)
        val btnImport = findViewById<Button>(R.id.btnImport)
        val btnStartPanel = findViewById<Button>(R.id.btnStartPanel)

        val btnPermissionsHelp = findViewById<Button>(R.id.btnPermissionsHelp)
        val btnInfoHelp = findViewById<Button>(R.id.btnInfoHelp)
        btnInfoHelp?.text = "Справка v28.11.0 PRO"
        val btnShowLogs = findViewById<Button>(R.id.btnShowLogs)
        val btnManageTemplates = findViewById<Button>(R.id.btnManageTemplates)

        btnAppDetails.setOnClickListener {
            val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            }
            startActivity(intent)
            Toast.makeText(this, "Прокрутите вниз -> Разрешить запрещенные настройки", Toast.LENGTH_LONG).show()
        }

        btnAccessibility.setOnClickListener {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            startActivity(intent)
            if (isAccessibilityServiceEnabled() && MyAutoClickService.instance == null) {
                Toast.makeText(this, "Выключите и включите тумблер AutoTap для перезапуска службы!", Toast.LENGTH_LONG).show()
            }
        }

        btnOverlay.setOnClickListener {
            try {
                val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
                startActivity(intent)
            } catch (e: Exception) {
                MyAutoClickService.logError(this, e)
                val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
                startActivity(intent)
            }
        }

        btnExport.setOnClickListener {
            showExportSelectionDialog()
        }

        btnImport.setOnClickListener {
            val prefs = getSharedPreferences("autotap_settings", Context.MODE_PRIVATE)
            val lastUriStr = prefs.getString("last_import_folder_uri", null)

            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                type = "application/zip"
                addCategory(Intent.CATEGORY_OPENABLE)
                if (lastUriStr != null) {
                    try {
                        putExtra("android.provider.extra.INITIAL_URI", Uri.parse(lastUriStr))
                    } catch (_: Exception) {}
                }
            }
            try {
                startActivityForResult(intent, 1002)
            } catch (_: Exception) {
                val fallbackIntent = Intent(Intent.ACTION_GET_CONTENT).apply {
                    type = "application/zip"
                    addCategory(Intent.CATEGORY_OPENABLE)
                }
                startActivityForResult(fallbackIntent, 1002)
            }
        }

        btnPermissionsHelp.setOnClickListener { showPermissionsHelpDialog() }
        btnInfoHelp.setOnClickListener { showInfoHelpDialog() }
        btnShowLogs.setOnClickListener { showLogsDialog() }
        btnManageTemplates.setOnClickListener { showTemplatesManagerDialog() }

        btnStartPanel.setOnClickListener {
            val service = MyAutoClickService.instance

            if (service == null) {
                if (isAccessibilityServiceEnabled()) {
                    Toast.makeText(this, "⚠️ Служба зависла в ОС после перезапуска! Выключите и включите тумблер в настройках.", Toast.LENGTH_LONG).show()
                } else {
                    Toast.makeText(this, "Сначала включите службу кликера (Шаг 2)!", Toast.LENGTH_SHORT).show()
                }
                val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                startActivity(intent)
                return@setOnClickListener
            }

            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Сначала разрешите показ поверх окон (Шаг 3)!", Toast.LENGTH_SHORT).show()
                showPermissionsHelpDialog()
                return@setOnClickListener
            }

            service.showControlPanel()
            moveTaskToBack(true)
        }
    }

    override fun onResume() {
        super.onResume()
        updatePermissionButtonStates()

        val isServiceRunning = MyAutoClickService.instance != null
        val isOverlayGranted = Settings.canDrawOverlays(this)

        if ((!isServiceRunning || !isOverlayGranted) && !hasAutoShownPermissions) {
            hasAutoShownPermissions = true
            showPermissionsHelpDialog()
        }
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val am = getSystemService(Context.ACCESSIBILITY_SERVICE) as? android.view.accessibility.AccessibilityManager
        if (am != null) {
            val enabledServices = am.getEnabledAccessibilityServiceList(
                android.accessibilityservice.AccessibilityServiceInfo.FEEDBACK_GENERIC or
                        android.accessibilityservice.AccessibilityServiceInfo.FEEDBACK_ALL_MASK
            )
            for (service in enabledServices) {
                if (service.resolveInfo.serviceInfo.packageName == packageName) {
                    return true
                }
            }
        }
        val enabledServicesStr = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: ""
        return enabledServicesStr.split(':').any { component ->
            component.substringBefore('/').equals(packageName, ignoreCase = true)
        }
    }

    private fun updatePermissionButtonStates() {
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)

        val isServiceBound = MyAutoClickService.instance != null
        val isSystemEnabled = isAccessibilityServiceEnabled()
        val isOverlayGranted = Settings.canDrawOverlays(this)

        if (btnAccessibility != null) {
            if (isServiceBound) {
                btnAccessibility.text = "2. Служба кликера: ВКЛЮЧЕНА ✅"
                btnAccessibility.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#1E3A2B"))
            } else if (isSystemEnabled) {
                btnAccessibility.text = "2. Перезапустить службу ⚠️ (Перевключите)"
                btnAccessibility.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#8B0000"))
            } else {
                btnAccessibility.text = "2. Разрешить работу кликера ⚠️"
                btnAccessibility.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#21262D"))
            }
        }

        if (btnOverlay != null) {
            if (isOverlayGranted) {
                btnOverlay.text = "3. Показ поверх окон: РАЗРЕШЕНО ✅"
                btnOverlay.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#1E3A2B"))
            } else {
                btnOverlay.text = "3. Поверх других приложений ⚠️"
                btnOverlay.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#21262D"))
            }
        }
    }

    private fun showExportSelectionDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_export_select, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        val btnSingle = dialogView.findViewById<Button>(R.id.btnExpSingleScript)
        val btnChain = dialogView.findViewById<Button>(R.id.btnExpChainScripts)
        val btnTemplates = dialogView.findViewById<Button>(R.id.btnExpTemplatesOnly)
        val btnBackup = dialogView.findViewById<Button>(R.id.btnExpFullBackup)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseExpSelect)

        btnSingle.setOnClickListener {
            ad.dismiss()
            showScriptPickerForExport(isChain = false)
        }

        btnChain.setOnClickListener {
            ad.dismiss()
            showScriptPickerForExport(isChain = true)
        }

        btnTemplates.setOnClickListener {
            ad.dismiss()
            exportTemplatesOnly()
        }

        btnBackup.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showScriptPickerForExport(isChain: Boolean) {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_select_script_for_export, null)
        val tvTitle = dialogView.findViewById<TextView>(R.id.tvPickerTitle)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutPickerList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnClosePicker)

        val ad = AlertDialog.Builder(this).setView(dialogView).create()
        tvTitle.text = if (isChain) "Выберите Главный сценарий цепочки" else "Выберите сценарий для экспорта"

        val dir = File(filesDir, "scripts")
        if (dir.exists()) {
            dir.listFiles()?.forEach { file ->
                if (file.name.endsWith(".json")) {
                    val btn = Button(this).apply {
                        text = file.nameWithoutExtension
                        setTextColor(Color.WHITE)
                        setBackgroundColor(getColor(R.color.panel_blue))
                        setOnClickListener {
                            ad.dismiss()
                            if (isChain) {
                                exportScriptChainPackage(file.nameWithoutExtension)
                            } else {
                                MyAutoClickService.instance?.exportScriptWithTemplates(this@MainActivity, file.nameWithoutExtension)
                            }
                        }
                    }
                    layoutList.addView(btn)
                }
            }
        }
        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun exportTemplatesOnly() {
        val baseDir = File(filesDir, "templates")
        if (!baseDir.exists() || baseDir.listFiles()?.isEmpty() == true) {
            Toast.makeText(this, "Пул ИИ-шаблонов пуст!", Toast.LENGTH_SHORT).show()
            return
        }
        val zipFile = File(externalCacheDir ?: cacheDir, "autotap_templates_only.zip")
        zipFolder(baseDir, zipFile)
        shareZipFile(zipFile, "ИИ-шаблоны AutoTap")
    }

    private fun exportFullBackup() {
        try {
            val zipFile = File(externalCacheDir ?: cacheDir, "autotap_full_backup.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val scriptsDir = File(filesDir, "scripts")
            if (scriptsDir.exists()) zipDirToZip(filesDir, scriptsDir, zos)

            val templatesDir = File(filesDir, "templates")
            if (templatesDir.exists()) zipDirToZip(filesDir, templatesDir, zos)

            zos.close()
            shareZipFile(zipFile, "Полный бэкап AutoTap")
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка создания бэкапа!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun exportScriptChainPackage(mainScriptName: String) {
        try {
            val scriptsDir = File(filesDir, "scripts")
            val scriptFile = File(scriptsDir, "$mainScriptName.json")
            if (!scriptFile.exists()) return

            val zipFile = File(externalCacheDir ?: cacheDir, "chain_$mainScriptName.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val scriptsToZip = HashSet<String>()
            val templatesToZip = HashSet<String>()

            fun traceScriptChain(sName: String) {
                if (sName.isEmpty() || scriptsToZip.contains(sName)) return
                scriptsToZip.add(sName)

                val file = File(scriptsDir, "$sName.json")
                if (file.exists()) {
                    val jsonArray = runCatching { JSONArray(file.readText()) }.getOrNull() ?: return
                    for (i in 0 until jsonArray.length()) {
                        val obj = jsonArray.optJSONObject(i) ?: continue
                        val tPath = obj.optString("templatePath", "")
                        val fPath = obj.optString("fullScreenshotPath", "")
                        val nextSc = obj.optString("targetScriptToLoad", "")

                        if (tPath.isNotEmpty()) templatesToZip.add(tPath)
                        if (fPath.isNotEmpty()) templatesToZip.add(fPath)
                        if (nextSc.isNotEmpty()) traceScriptChain(nextSc)
                    }
                }
            }

            traceScriptChain(mainScriptName)

            scriptsToZip.forEach { scName ->
                val f = File(scriptsDir, "$scName.json")
                if (f.exists()) {
                    val entry = ZipEntry("scripts/$scName.json")
                    zos.putNextEntry(entry)
                    zos.write(f.readBytes())
                    zos.closeEntry()
                }
            }

            templatesToZip.forEach { imgPath ->
                val imgFile = if (File(imgPath).isAbsolute) File(imgPath) else File(filesDir, imgPath)
                if (imgFile.exists()) {
                    val dateFolder = imgFile.parentFile?.name ?: "default"
                    val entryName = "templates/$dateFolder/${imgFile.name}"
                    val entry = ZipEntry(entryName)
                    zos.putNextEntry(entry)
                    zos.write(imgFile.readBytes())
                    zos.closeEntry()

                    val metaFile = File(imgFile.parentFile, "${imgFile.nameWithoutExtension}.json")
                    if (metaFile.exists()) {
                        val metaEntryName = "templates/$dateFolder/${metaFile.name}"
                        val metaEntry = ZipEntry(metaEntryName)
                        zos.putNextEntry(metaEntry)
                        zos.write(metaFile.readBytes())
                        zos.closeEntry()
                    }
                }
            }
            zos.close()

            shareZipFile(zipFile, "Цепочка сценариев: $mainScriptName")
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка экспорта цепочки!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun zipDirToZip(rootFolder: File, srcFolder: File, zos: ZipOutputStream) {
        val files = srcFolder.listFiles() ?: return
        for (file in files) {
            if (file.isDirectory) {
                zipDirToZip(rootFolder, file, zos)
            } else {
                val entryName = file.absolutePath.substring(rootFolder.absolutePath.length + 1)
                val entry = ZipEntry(entryName)
                zos.putNextEntry(entry)
                BufferedInputStream(FileInputStream(file)).use { bis ->
                    bis.copyTo(zos)
                }
                zos.closeEntry()
            }
        }
    }

    private fun shareZipFile(zipFile: File, title: String) {
        val uri = try {
            FileProvider.getUriForFile(this, "$packageName.fileprovider", zipFile)
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            null
        }
        if (uri == null) {
            Toast.makeText(this, "Не удалось сформировать ссылку на файл!", Toast.LENGTH_SHORT).show()
            return
        }
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_SUBJECT, title)
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(shareIntent, title))
    }

    private fun showTemplatesManagerDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_templates_manager, null)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutTemplatesList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseTemplatesManager)

        val btnOpenTrashBin = dialogView.findViewById<Button>(R.id.btnOpenTrashBin)
        btnOpenTrashBin?.setOnClickListener { showTrashBinDialog() }

        val ad = AlertDialog.Builder(this)
            .setView(dialogView)
            .create()

        fun refreshTemplatesList() {
            layoutList.removeAllViews()
            val baseDir = File(filesDir, "templates")
            if (baseDir.exists()) {
                val dateFolders = baseDir.listFiles()
                dateFolders?.forEach { folder ->
                    if (folder.isDirectory) {
                        val images = folder.listFiles()
                        images?.forEach { file ->
                            if (file.name.startsWith("mask_") && file.name.endsWith(".png")) {
                                val itemView = LayoutInflater.from(this@MainActivity).inflate(R.layout.item_template, null)
                                val ivPreview = itemView.findViewById<ImageView>(R.id.ivTemplatePreview)
                                val tvName = itemView.findViewById<TextView>(R.id.tvTemplateName)
                                val btnEditMask = itemView.findViewById<Button>(R.id.btnEditTemplateMask)
                                val btnDelete = itemView.findViewById<Button>(R.id.btnDeleteTemplateFile)

                                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                                ivPreview.setImageBitmap(bitmap)
                                val meta: JSONObject? = MyAutoClickService.instance?.loadTemplateMetadata(file.absolutePath)
                                val pctStr = if (meta != null && meta.has("similarityPercent")) " (🎯 " + meta.getInt("similarityPercent") + "%)" else ""
                                tvName.text = "${folder.name}\n${file.nameWithoutExtension}$pctStr"

                                btnEditMask?.setOnClickListener {
                                    showMaskEditorDialog(file) {
                                        refreshTemplatesList()
                                        MyAutoClickService.instance?.loadAllTemplatesFromDisk()
                                    }
                                }

                                btnDelete.setOnClickListener {
                                    val idx = MyAutoClickService.instance?.globalTemplatesNames?.indexOf(file.absolutePath) ?: -1
                                    if (idx != -1) {
                                        MyAutoClickService.instance?.moveTemplateToTrash(idx)
                                    } else {
                                        file.delete()
                                    }
                                    refreshTemplatesList()
                                    MyAutoClickService.instance?.loadAllTemplatesFromDisk()
                                    Toast.makeText(this@MainActivity, "Шаблон перемещен в корзину!", Toast.LENGTH_SHORT).show()
                                }
                                layoutList.addView(itemView)
                            }
                        }
                    }
                }
            }
            if (layoutList.childCount == 0) {
                val emptyTv = TextView(this@MainActivity).apply {
                    text = "Пул ИИ-шаблонов пуст. Запишите шаблоны кнопкой 📷"
                    setTextColor(resources.getColor(R.color.text_gray))
                    textSize = 13f
                    setPadding(10, 10, 10, 10)
                }
                layoutList.addView(emptyTv)
            }
        }

        refreshTemplatesList()
        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showTrashBinDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_scripts, null)
        val tvTitle = dialogView.findViewById<TextView>(R.id.tvScriptTitle)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutScriptsList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseScripts)
        val btnSaveAction = dialogView.findViewById<Button>(R.id.btnSaveScriptAction)
        val etScriptName = dialogView.findViewById<View>(R.id.etScriptName)

        btnSaveAction?.visibility = View.GONE
        etScriptName?.visibility = View.GONE

        val ad = AlertDialog.Builder(this).setView(dialogView).create()
        tvTitle.text = "🗑 Корзина удаленных масок"

        fun refreshTrashList() {
            layoutList.removeAllViews()
            val trashDir = File(filesDir, "trash_templates")
            val now = System.currentTimeMillis()
            val sevenDaysMs = 7L * 24 * 60 * 60 * 1000L

            if (trashDir.exists()) {
                val dateFolders = trashDir.listFiles()
                dateFolders?.forEach { folder ->
                    if (folder.isDirectory) {
                        val images = folder.listFiles()
                        images?.forEach { file ->
                            if (file.name.startsWith("mask_") && file.name.endsWith(".png")) {
                                val itemView = LayoutInflater.from(this@MainActivity).inflate(R.layout.item_template, null)
                                val ivPreview = itemView.findViewById<ImageView>(R.id.ivTemplatePreview)
                                val tvName = itemView.findViewById<TextView>(R.id.tvTemplateName)
                                val btnRestore = itemView.findViewById<Button>(R.id.btnEditTemplateMask)
                                val btnDeletePermanently = itemView.findViewById<Button>(R.id.btnDeleteTemplateFile)

                                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                                ivPreview.setImageBitmap(bitmap)

                                val elapsedMs = now - file.lastModified()
                                val remainingDays = ((sevenDaysMs - elapsedMs) / (1000 * 60 * 60 * 24)).coerceAtLeast(0)
                                tvName.text = "${file.nameWithoutExtension}\n(Удалится через $remainingDays дн)"

                                btnRestore?.text = "♻️"
                                btnRestore?.setOnClickListener {
                                    restoreTemplateFromTrash(file)
                                    refreshTrashList()
                                }

                                btnDeletePermanently.setOnClickListener {
                                    val timestamp = file.name.removePrefix("mask_").removeSuffix(".png")
                                    val fullFile = File(folder, "full_${timestamp}.png")
                                    val metaFile = File(folder, "${file.nameWithoutExtension}.json")
                                    file.delete()
                                    if (fullFile.exists()) fullFile.delete()
                                    if (metaFile.exists()) metaFile.delete()
                                    refreshTrashList()
                                    Toast.makeText(this@MainActivity, "Удалено окончательно!", Toast.LENGTH_SHORT).show()
                                }

                                layoutList.addView(itemView)
                            }
                        }
                    }
                }
            }

            if (layoutList.childCount == 0) {
                val emptyTv = TextView(this@MainActivity).apply {
                    text = "Корзина пуста!"
                    setTextColor(resources.getColor(R.color.text_gray))
                    textSize = 13f
                    setPadding(10, 10, 10, 10)
                }
                layoutList.addView(emptyTv)
            }
        }

        refreshTrashList()
        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun restoreTemplateFromTrash(trashMaskFile: File) {
        try {
            val dateFolder = trashMaskFile.parentFile?.name ?: "default"
            val timestamp = trashMaskFile.name.removePrefix("mask_").removeSuffix(".png")
            val trashFullFile = File(trashMaskFile.parentFile, "full_${timestamp}.png")

            val targetDir = File(File(filesDir, "templates"), dateFolder).apply { mkdirs() }

            val restoredMask = File(targetDir, trashMaskFile.name)
            trashMaskFile.renameTo(restoredMask)

            if (trashFullFile.exists()) {
                val restoredFull = File(targetDir, trashFullFile.name)
                trashFullFile.renameTo(restoredFull)
            }

            MyAutoClickService.instance?.loadAllTemplatesFromDisk()
            Toast.makeText(this, "♻️ Шаблон успешно восстановлен из корзины!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
        }
    }

    private fun showMaskEditorDialog(maskFile: File, onDone: () -> Unit) {
        val dateFolder = maskFile.parentFile ?: return
        val maskName = maskFile.name
        val timestamp = maskName.removePrefix("mask_").removeSuffix(".png")
        val fullScreenshotFile = File(dateFolder, "full_${timestamp}.png")

        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_mask_editor, null)
        val ivFull = dialogView.findViewById<ImageView>(R.id.ivEditorFullScreenshot)
        val ivMask = dialogView.findViewById<ImageView>(R.id.ivEditorMaskPreview)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSaveMaskEdits)
        val btnCopy = dialogView.findViewById<Button>(R.id.btnCopyMaskEdits)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancelMaskEdits)

        val btnToggleShape = dialogView.findViewById<Button>(R.id.btnToggleMaskShape)
        val btnWidthMinus = dialogView.findViewById<Button>(R.id.btnCropWidthMinus)
        val btnWidthPlus = dialogView.findViewById<Button>(R.id.btnCropWidthPlus)
        val btnHeightPlus = dialogView.findViewById<Button>(R.id.btnCropHeightPlus)
        val tvCropDisplay = dialogView.findViewById<TextView>(R.id.tvCropSizeDisplay)

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        val btnCloseHeader = dialogView.findViewById<ImageButton>(R.id.btnCloseMaskEditor)
        btnCloseHeader?.setOnClickListener {
            ad.dismiss()
            onDone()
        }

        val maskBitmap = BitmapFactory.decodeFile(maskFile.absolutePath)
        ivMask.setImageBitmap(maskBitmap)

        var cropW = maskBitmap?.width ?: 100
        var cropH = maskBitmap?.height ?: 100
        var isCircle = true

        fun updateSizeDisplay() {
            tvCropDisplay?.text = "📏 ${cropW}x${cropH} px"
        }
        updateSizeDisplay()

        btnToggleShape?.setOnClickListener {
            isCircle = !isCircle
            btnToggleShape.text = if (isCircle) "Форма: 🔘 Круг" else "Форма: 🔲 Прямоугольник"
        }

        btnWidthMinus?.setOnClickListener {
            cropW = (cropW - 20).coerceAtLeast(20)
            updateSizeDisplay()
        }

        btnWidthPlus?.setOnClickListener {
            cropW = (cropW + 20).coerceAtMost(1000)
            updateSizeDisplay()
        }

        btnHeightPlus?.setOnClickListener {
            cropH = (cropH + 20).coerceAtMost(1000)
            updateSizeDisplay()
        }

        if (fullScreenshotFile.exists()) {
            val fullBitmap = BitmapFactory.decodeFile(fullScreenshotFile.absolutePath)
            ivFull.setImageBitmap(fullBitmap)

            var currentCropped: Bitmap? = null

            ivFull.setOnTouchListener { v, event ->
                if (event.action == MotionEvent.ACTION_UP && fullBitmap != null) {
                    val vW = v.width
                    val vH = v.height
                    if (vW > 0 && vH > 0) {
                        val bmpW = fullBitmap.width
                        val bmpH = fullBitmap.height

                        val scale = Math.min(vW.toFloat() / bmpW, vH.toFloat() / bmpH)
                        val actualW = bmpW * scale
                        val actualH = bmpH * scale

                        val leftOffset = (vW - actualW) / 2f
                        val topOffset = (vH - actualH) / 2f

                        val touchX = event.x - leftOffset
                        val touchY = event.y - topOffset

                        if (touchX >= 0 && touchX <= actualW && touchY >= 0 && touchY <= actualH) {
                            val realX = (touchX / scale).toInt()
                            val realY = (touchY / scale).toInt()

                            val cropX = (realX - cropW / 2).coerceIn(0, (bmpW - cropW).coerceAtLeast(0))
                            val cropY = (realY - cropH / 2).coerceIn(0, (bmpH - cropH).coerceAtLeast(0))

                            val rawCropped = Bitmap.createBitmap(fullBitmap, cropX, cropY, cropW.coerceAtMost(bmpW - cropX), cropH.coerceAtMost(bmpH - cropY))
                            currentCropped = TemplateMatcher.generateSmartMask(rawCropped, isCircle)
                            ivMask.setImageBitmap(currentCropped)
                        }
                    }
                }
                true
            }

            btnSave.setOnClickListener {
                val croppedToSave = currentCropped
                if (croppedToSave != null) {
                    try {
                        FileOutputStream(maskFile).use { out ->
                            croppedToSave.compress(Bitmap.CompressFormat.PNG, 100, out)
                        }
                        Toast.makeText(this, "Маска успешно обновлена!", Toast.LENGTH_SHORT).show()
                    } catch (e: Exception) {
                        MyAutoClickService.logError(this, e)
                    }
                }
                ad.dismiss()
                onDone()
            }

            btnCopy.setOnClickListener {
                val croppedToSave = currentCropped ?: maskBitmap
                if (croppedToSave != null) {
                    try {
                        val ts = System.currentTimeMillis()
                        val copyMask = File(dateFolder, "mask_${ts}.png")
                        FileOutputStream(copyMask).use { out ->
                            croppedToSave.compress(Bitmap.CompressFormat.PNG, 100, out)
                        }
                        if (fullScreenshotFile.exists()) {
                            val copyFull = File(dateFolder, "full_${ts}.png")
                            fullScreenshotFile.copyTo(copyFull, overwrite = true)
                        }
                        Toast.makeText(this, "📋 Создана копия шаблона!", Toast.LENGTH_SHORT).show()
                    } catch (e: Exception) {
                        MyAutoClickService.logError(this, e)
                    }
                }
                ad.dismiss()
                onDone()
            }
        } else {
            Toast.makeText(this, "Фоновый скриншот не найден для этой маски", Toast.LENGTH_SHORT).show()
        }

        btnCancel.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showLogsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_logs, null)
        val tvLogsContent = dialogView.findViewById<TextView>(R.id.tvLogsContent)
        val btnShareLogs = dialogView.findViewById<Button>(R.id.btnShareLogs)
        val btnClearLogs = dialogView.findViewById<Button>(R.id.btnClearLogs)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseLogs)

        val ad = AlertDialog.Builder(this)
            .setView(dialogView)
            .create()

        val logFile = File(filesDir, "error_log.txt")
        if (logFile.exists()) {
            tvLogsContent.text = logFile.readText()
        } else {
            tvLogsContent.text = "Логи пусты. Ошибок не зафиксировано!"
        }

        btnShareLogs?.setOnClickListener {
            if (logFile.exists() && logFile.length() > 0) {
                try {
                    val shareIntent = Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_SUBJECT, "AutoTap Error Log")
                        putExtra(Intent.EXTRA_TEXT, logFile.readText())
                    }
                    startActivity(Intent.createChooser(shareIntent, "Поделиться логом ошибок"))
                    ad.dismiss()
                } catch (e: Exception) {
                    MyAutoClickService.logError(this@MainActivity, e)
                    Toast.makeText(this@MainActivity, "Ошибка отправки лога!", Toast.LENGTH_SHORT).show()
                }
            } else {
                Toast.makeText(this@MainActivity, "Лог файл пуст!", Toast.LENGTH_SHORT).show()
            }
        }

        btnClearLogs.setOnClickListener {
            if (logFile.exists()) logFile.writeText("")
            tvLogsContent.text = "Логи пусты. Ошибок не зафиксировано!"
            Toast.makeText(this, "Лог ошибок успешно очищен!", Toast.LENGTH_SHORT).show()
        }

        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showPermissionsHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_permissions, null)
        val tvDevicePath = dialogView.findViewById<TextView>(R.id.tvDevicePath)
        val btnClose = dialogView.findViewById<Button>(R.id.btnClosePermissionsDialog)

        val ad = AlertDialog.Builder(this)
            .setView(dialogView)
            .create()

        val manufacturer = android.os.Build.MANUFACTURER.lowercase(Locale.US)
        val model = android.os.Build.MODEL

        val pathText = when {
            manufacturer.contains("xiaomi") || manufacturer.contains("poco") || manufacturer.contains("redmi") -> {
                """Устройство: $model (MIUI / HyperOS)

1. Шаг 1 ("Запрещенные настройки"):
Нажмите "1. Разрешить запрещенные настройки" -> Прокрутите в самый низ -> Включите 'Разрешить запрещенные настройки'. (В 'Контроль активности' выберите 'Нет ограничений').

2. Шаг 2 ("Служба кликера"):
Нажмите "2. Разрешить работу кликера" -> Настройки -> Специальные возможности -> Скачанные приложения -> AutoTap -> Включите тумблер.

3. Шаг 3 ("Поверх других окон"):
Нажмите "3. Поверх других приложений" -> Найдите AutoTap -> Разрешите показ поверх других окон."""
            }
            manufacturer.contains("samsung") -> {
                """Устройство: $model (OneUI)

1. Шаг 1 ("Свойства приложения"):
Нажмите "1. Разрешить запрещенные настройки" для перехода в свойства приложения.

2. Шаг 2 ("Служба кликера"):
Нажмите "2. Разрешить работу кликера" -> Специальные возможности -> Установленные приложения -> AutoTap -> Включите службу.

3. Шаг 3 ("Поверх других окон"):
Нажмите "3. Поверх других приложений" -> Разрешите показ поверх других окон."""
            }
            manufacturer.contains("huawei") || manufacturer.contains("honor") -> {
                """Устройство: $model (EMUI / MagicUI)

1. Шаг 1 ("Свойства приложения"):
Нажмите "1. Разрешить запрещенные настройки" -> Запуск приложений -> Отключите автоуправление.

2. Шаг 2 ("Служба кликера"):
Нажмите "2. Разрешить работу кликера" -> Специальные возможности -> Установленные службы -> AutoTap -> Включите службу.

3. Шаг 3 ("Поверх других окон"):
Нажмите "3. Поверх других приложений" -> Разрешите наложение поверх окон."""
            }
            else -> {
                """Устройство: $model (Android)

1. Шаг 1 ("Свойства приложения"):
Нажмите "1. Разрешить запрещенные настройки" для сброса ограничений батареи.

2. Шаг 2 ("Служба кликера"):
Нажмите "2. Разрешить работу кликера" -> Специальные возможности -> Скачанные службы -> AutoTap -> Включите службу.

3. Шаг 3 ("Поверх других окон"):
Нажмите "3. Поверх других приложений" -> Разрешите показ поверх всех окон."""
            }
        }

        tvDevicePath.text = pathText
        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showInfoHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_info, null)
        val tabClick = dialogView.findViewById<Button>(R.id.tabClick)
        val tabSwipe = dialogView.findViewById<Button>(R.id.tabSwipe)
        val tabAi = dialogView.findViewById<Button>(R.id.tabAi)
        val tvContent = dialogView.findViewById<TextView>(R.id.tvTabContent)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseInfoDialog)

        val ad = AlertDialog.Builder(this)
            .setView(dialogView)
            .create()

        fun selectTab(tab: String) {
            tabClick.setTextColor(Color.WHITE)
            tabSwipe.setTextColor(Color.WHITE)
            tabAi.setTextColor(Color.WHITE)
            tabClick.setBackgroundColor(getColor(if (tab == "click") R.color.accent_blue else R.color.bg_dark_blue))
            tabSwipe.setBackgroundColor(getColor(if (tab == "swipe") R.color.accent_blue else R.color.bg_dark_blue))
            tabAi.setBackgroundColor(getColor(if (tab == "ai") R.color.accent_blue else R.color.bg_dark_blue))

            tvContent.text = when(tab) {
                "click" -> """НАЖАТИЯ И НАВИГАЦИЯ v28.11.0 PRO:
1. Добавляйте мишени кнопкой '+' или нативную запись '●' со скоростью 60 FPS.
2. Неоновая анимация ✨ визуально подсвечивает место и момент каждого тапа.
3. Тактильная отдача 📳: Приятный физический виброотклик при снимках и фиксации %.
4. Защита от античитов 🎲: Человеческая микро-рандомизация задержки (Jitter) предотвращает блокировки в играх.
5. Защита экрана 🌙: экран устройства не выключается во время работы."""

                "swipe" -> """ЖЕСТЫ И ДЖОЙСТИК v28.11.0 PRO:
1. Джойстик 🕹 зажимает и ведает плавной непрерывной траекторией движения (Path Gesture).
2. Настройка времени удержания, скольжения и направления.
3. Во время воспроизведения джойстик автоматически скрывается, предотвращая фантомные клики."""

                else -> """ИИ-СКАНИРОВАНИЕ И МУЛЬТИПОИСК v28.11.0 PRO:
1. Авто-калибровка 📸: Сразу после вырезания маски запускается чистое сканирование экрана и фиксация %.
2. Непрерывный мультипоиск 🔄: Одиночный или финальный ИИ-шаг сканирует экран каждые 2 секунды без таймаута до кнопки СТОП.
3. Каскадная точность ⚡: 3-этапный поиск проверяет личный % маски, допуск -8% и минимальный % шага.
4. Выбор точки клика 🎯: Переключение клика 'В точку совпадения ИИ' или 'По коорд. мишени шага'."""
            }
        }

        selectTab("click")

        tabClick.setOnClickListener { selectTab("click") }
        tabSwipe.setOnClickListener { selectTab("swipe") }
        tabAi.setOnClickListener { selectTab("ai") }

        btnClose.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1002 && resultCode == RESULT_OK && data != null) {
            val zipUri = data.data ?: return
            try {
                getSharedPreferences("autotap_settings", Context.MODE_PRIVATE).edit {
                    putString("last_import_folder_uri", zipUri.toString())
                }
                val inputStream = contentResolver.openInputStream(zipUri) ?: return
                val tempZipFile = File(cacheDir, "temp_import.zip")

                FileOutputStream(tempZipFile).use { out ->
                    inputStream.copyTo(out)
                }

                val zis = ZipInputStream(BufferedInputStream(FileInputStream(tempZipFile)))
                unzipPackage(zis)
                zis.close()
            } catch (e: Exception) {
                MyAutoClickService.logError(this, e)
                Toast.makeText(this, "Ошибка импорта! Убедитесь, что выбрали ZIP.", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun zipFolder(srcFolder: File, destZipFile: File) {
        ZipOutputStream(BufferedOutputStream(FileOutputStream(destZipFile))).use { zos ->
            zipDir(srcFolder, srcFolder, zos)
        }
    }

    private fun zipDir(rootFolder: File, srcFolder: File, zos: ZipOutputStream) {
        val files = srcFolder.listFiles() ?: return
        for (file in files) {
            if (file.isDirectory) {
                zipDir(rootFolder, file, zos)
            } else {
                val entryName = file.absolutePath.substring(rootFolder.absolutePath.length + 1)
                val entry = ZipEntry(entryName)
                zos.putNextEntry(entry)
                BufferedInputStream(FileInputStream(file)).use { bis ->
                    bis.copyTo(zos)
                }
                zos.closeEntry()
            }
        }
    }

    private fun unzipPackage(zipInputStream: ZipInputStream) {
        try {
            var entry = zipInputStream.nextEntry
            while (entry != null) {
                val entryName = entry.name
                if (!entry.isDirectory) {
                    val outFile: File = if (entryName.startsWith("scripts/")) {
                        val fileName = entryName.substringAfterLast("/")
                        File(File(filesDir, "scripts").apply { mkdirs() }, fileName)
                    } else if (entryName.startsWith("templates/")) {
                        val subPath = entryName.removePrefix("templates/")
                        File(File(filesDir, "templates").apply { mkdirs() }, subPath).apply { parentFile?.mkdirs() }
                    } else {
                        File(filesDir, entryName)
                    }

                    outFile.parentFile?.mkdirs()
                    FileOutputStream(outFile).use { out ->
                        zipInputStream.copyTo(out)
                    }
                }
                zipInputStream.closeEntry()
                entry = zipInputStream.nextEntry
            }
            MyAutoClickService.instance?.loadAllTemplatesFromDisk()
            Toast.makeText(this, "🎉 Сценарий и все ИИ-шаблоны успешно импортированы!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка импорта пакета!", Toast.LENGTH_SHORT).show()
        }
    }
}
