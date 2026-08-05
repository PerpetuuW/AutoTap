import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Развернут модуль v40 Master: {rel_path}")

def deploy_v40_ultimate_master():
    print("🚀 Внедрение главной системной конфигурации и защиты от усыпления v40.0.0-PRO...")

    # 1. app/build.gradle.kts
    gradle_code = r"""plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.autotap"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.autotap"
        minSdk = 24
        targetSdk = 35
        versionCode = 2800
        versionName = "40.0.0-PRO"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("com.google.android.material:material:1.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
"""
    write_file("app/build.gradle.kts", gradle_code)

    # 2. AndroidManifest.xml (Разрешение отмены оптимизации батареи)
    manifest_code = r"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="AutoTap v40"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.DayNight.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".MyAutoClickService"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
            android:exported="false">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>

</manifest>
"""
    write_file("app/src/main/AndroidManifest.xml", manifest_code)

    # 3. accessibility_service_config.xml (Полная конфигурация жестов и скриншотов)
    accessibility_config_code = r"""<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeAllMask"
    android:accessibilityFeedbackType="feedbackGeneric"
    android:accessibilityFlags="flagDefault|flagIncludeNotImportantViews|flagReportViewIds|flagRetrieveInteractiveWindows"
    android:canPerformGestures="true"
    android:canTakeScreenshot="true"
    android:description="@string/accessibility_description" />
"""
    write_file("app/src/main/res/xml/accessibility_service_config.xml", accessibility_config_code)

    # 4. MainActivity.kt (Запрос отключения оптимизации батареи + Инструкция Xiaomi/HyperOS)
    main_activity_code = r"""package com.example.autotap

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.os.StrictMode
import android.provider.Settings
import android.view.LayoutInflater
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import java.io.*
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

@Suppress("SpellCheckingInspection", "DEPRECATION")
class MainActivity : AppCompatActivity() {

    private var hasAutoShownPermissions = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        StrictMode.setVmPolicy(StrictMode.VmPolicy.Builder().build())

        val tvVersion = findViewById<TextView>(R.id.tvVersion)
        tvVersion?.text = "AutoTap v40.0.0-PRO"

        val btnAppDetails = findViewById<Button>(R.id.btnAppDetails)
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)
        val btnExport = findViewById<Button>(R.id.btnExport)
        val btnImport = findViewById<Button>(R.id.btnImport)
        val btnStartPanel = findViewById<Button>(R.id.btnStartPanel)
        val btnShowLogs = findViewById<Button>(R.id.btnShowLogs)
        val btnManageTemplates = findViewById<Button>(R.id.btnManageTemplates)
        val btnPermissionsHelp = findViewById<Button>(R.id.btnPermissionsHelp)
        val btnInfoHelp = findViewById<Button>(R.id.btnInfoHelp)

        btnAppDetails?.setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            })
        }

        btnAccessibility?.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        btnOverlay?.setOnClickListener {
            try {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            } catch (_: Exception) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION))
            }
        }

        btnExport?.setOnClickListener { showExportDialog() }
        btnImport?.setOnClickListener { startImportFlow() }
        btnShowLogs?.setOnClickListener { showLogsDialog() }
        btnManageTemplates?.setOnClickListener { showTemplatesManagerDialog() }
        btnPermissionsHelp?.setOnClickListener { showPermissionsHelpDialog() }
        btnInfoHelp?.setOnClickListener { showInfoHelpDialog() }

        btnStartPanel?.setOnClickListener {
            val service = MyAutoClickService.instance
            if (service == null) {
                Toast.makeText(this, "Служба не активна!", Toast.LENGTH_SHORT).show()
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                return@setOnClickListener
            }

            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Разрешите показ поверх окон!", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            requestBatteryOptimizationExemption()

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

    private fun requestBatteryOptimizationExemption() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(Context.POWER_SERVICE) as? PowerManager
            if (pm != null && !pm.isIgnoringBatteryOptimizations(packageName)) {
                try {
                    val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                        data = Uri.parse("package:$packageName")
                    }
                    startActivity(intent)
                } catch (_: Exception) {}
            }
        }
    }

    private fun updatePermissionButtonStates() {
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)

        val isServiceBound = MyAutoClickService.instance != null
        val isSystemEnabled = isAccessibilityServiceEnabled()
        val isOverlayGranted = Settings.canDrawOverlays(this)

        btnAccessibility?.text =
            if (isServiceBound) "Служба кликера: ВКЛЮЧЕНА"
            else if (isSystemEnabled) "Перезапустить службу"
            else "Разрешить работу кликера"

        btnAccessibility?.backgroundTintList =
            ColorStateList.valueOf(if (isServiceBound) Color.parseColor("#1E3A2B") else Color.parseColor("#8B0000"))

        btnOverlay?.text =
            if (isOverlayGranted) "Показ поверх окон: РАЗРЕШЕНО"
            else "Показ поверх окон: ОТКЛЮЧЕНО"

        btnOverlay?.backgroundTintList =
            ColorStateList.valueOf(if (isOverlayGranted) Color.parseColor("#1E3A2B") else Color.parseColor("#21262D"))
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val am = getSystemService(Context.ACCESSIBILITY_SERVICE) as? android.view.accessibility.AccessibilityManager
        val enabled = am?.getEnabledAccessibilityServiceList(
            android.accessibilityservice.AccessibilityServiceInfo.FEEDBACK_ALL_MASK
        ) ?: emptyList()

        if (enabled.any { it.resolveInfo.serviceInfo.packageName == packageName }) return true

        val raw = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: ""
        return raw.split(':').any { it.substringBefore('/').equals(packageName, true) }
    }

    private fun showExportDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_export_select, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        dialogView.findViewById<Button>(R.id.btnExpSingleScript)?.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        dialogView.findViewById<Button>(R.id.btnExpTemplatesOnly)?.setOnClickListener {
            ad.dismiss()
            exportTemplatesOnly()
        }

        dialogView.findViewById<Button>(R.id.btnExpFullBackup)?.setOnClickListener {
            ad.dismiss()
            exportFullBackup()
        }

        dialogView.findViewById<Button>(R.id.btnCloseExpSelect)?.setOnClickListener {
            ad.dismiss()
        }

        ad.show()
    }

    private fun exportTemplatesOnly() {
        val baseDir = File(filesDir, "templates")
        if (!baseDir.exists() || baseDir.listFiles()?.isEmpty() == true) {
            Toast.makeText(this, "Пул шаблонов пуст!", Toast.LENGTH_SHORT).show()
            return
        }

        val zipFile = File(externalCacheDir ?: cacheDir, "autotap_templates.zip")
        zipFolder(baseDir, zipFile)
        shareZip(zipFile, "ИИ-шаблоны AutoTap")
    }

    private fun exportFullBackup() {
        try {
            val zipFile = File(externalCacheDir ?: cacheDir, "autotap_backup.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val scriptsDir = File(filesDir, "scripts")
            if (scriptsDir.exists()) zipDirToZip(filesDir, scriptsDir, zos)

            val templatesDir = File(filesDir, "templates")
            if (templatesDir.exists()) zipDirToZip(filesDir, templatesDir, zos)

            zos.close()
            shareZip(zipFile, "Полный бэкап AutoTap v40.0")
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка бэкапа!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun startImportFlow() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            type = "application/zip"
            addCategory(Intent.CATEGORY_OPENABLE)
        }
        startActivityForResult(intent, 1002)
    }

    override fun onActivityResult(req: Int, res: Int, data: Intent?) {
        super.onActivityResult(req, res, data)
        if (req == 1002 && res == RESULT_OK) {
            val uri = data?.data ?: return
            importZip(uri)
        }
    }

    private fun importZip(uri: Uri) {
        try {
            val input = contentResolver.openInputStream(uri) ?: return
            val zis = ZipInputStream(BufferedInputStream(input))

            var entry: ZipEntry?
            val canonicalBase = filesDir.canonicalPath

            while (zis.nextEntry.also { entry = it } != null) {
                val name = entry!!.name
                val outFile = File(filesDir, name)

                if (!outFile.canonicalPath.startsWith(canonicalBase)) {
                    throw SecurityException("Заблокирована попытка записи Zip Slip файла вне каталога!")
                }

                outFile.parentFile?.mkdirs()
                BufferedOutputStream(FileOutputStream(outFile)).use { bos ->
                    zis.copyTo(bos)
                }
            }
            zis.close()

            MyAutoClickService.instance?.loadAllTemplatesFromDisk()
            Toast.makeText(this, "Импорт завершён!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(this, e)
            Toast.makeText(this, "Ошибка импорта!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun zipFolder(folder: File, zipFile: File) {
        val zos = ZipOutputStream(FileOutputStream(zipFile))
        folder.listFiles()?.forEach { file ->
            val entry = ZipEntry(file.name)
            zos.putNextEntry(entry)
            zos.write(file.readBytes())
            zos.closeEntry()
        }
        zos.close()
    }

    private fun zipDirToZip(root: File, src: File, zos: ZipOutputStream) {
        src.listFiles()?.forEach { file ->
            if (file.isDirectory) {
                zipDirToZip(root, file, zos)
            } else {
                val entryName = file.absolutePath.substring(root.absolutePath.length + 1)
                zos.putNextEntry(ZipEntry(entryName))
                zos.write(file.readBytes())
                zos.closeEntry()
            }
        }
    }

    private fun shareZip(zipFile: File, title: String) {
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", zipFile)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, title))
    }

    private fun showLogsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_logs, null)
        val tvLogs = dialogView.findViewById<TextView>(R.id.tvLogsContent)
        val btnShare = dialogView.findViewById<Button>(R.id.btnShareLogs)
        val btnClear = dialogView.findViewById<Button>(R.id.btnClearLogs)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseLogs)

        val logFile = File(filesDir, "error_log.txt")
        tvLogs?.text = if (logFile.exists() && logFile.length() > 0) logFile.readText() else "Логи отсутствуют."

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        btnShare?.setOnClickListener {
            if (logFile.exists() && logFile.length() > 0) {
                val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", logFile)
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                startActivity(Intent.createChooser(intent, "Поделиться логами"))
            } else {
                Toast.makeText(this, "Логи пусты", Toast.LENGTH_SHORT).show()
            }
        }

        btnClear?.setOnClickListener {
            if (logFile.exists()) logFile.delete()
            tvLogs?.text = "Логи очищены."
            Toast.makeText(this, "Логи очищены", Toast.LENGTH_SHORT).show()
        }

        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showTemplatesManagerDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_templates_manager, null)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutTemplatesList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseTemplatesManager)

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        fun refresh() {
            layoutList?.removeAllViews()
            val baseDir = File(filesDir, "templates")

            baseDir.listFiles()?.forEach { folder ->
                if (folder.isDirectory) {
                    folder.listFiles()?.forEach { file ->
                        if (file.name.startsWith("mask_") && file.name.endsWith(".png")) {
                            val item = LayoutInflater.from(this).inflate(R.layout.item_template, null)

                            val iv = item.findViewById<ImageView>(R.id.ivTemplatePreview)
                            val tv = item.findViewById<TextView>(R.id.tvTemplateName)
                            val btnDelete = item.findViewById<Button>(R.id.btnDeleteTemplateFile)

                            iv?.setImageBitmap(BitmapFactory.decodeFile(file.absolutePath))
                            tv?.text = "${folder.name}\n${file.nameWithoutExtension}"

                            btnDelete?.setOnClickListener {
                                MyAutoClickService.instance?.moveTemplateToTrash(
                                    MyAutoClickService.instance?.globalTemplatesNames?.indexOf(file.absolutePath) ?: -1
                                )
                                MyAutoClickService.instance?.loadAllTemplatesFromDisk()
                                refresh()
                            }

                            layoutList?.addView(item)
                        }
                    }
                }
            }
        }

        refresh()
        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showPermissionsHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_permissions, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()
        dialogView.findViewById<Button>(R.id.btnClosePermissionsDialog)?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showInfoHelpDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_info, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        val tvContent = dialogView.findViewById<TextView>(R.id.tvTabContent)
        val tabClick = dialogView.findViewById<Button>(R.id.tabClick)
        val tabSwipe = dialogView.findViewById<Button>(R.id.tabSwipe)
        val tabAi = dialogView.findViewById<Button>(R.id.tabAi)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseInfoDialog)

        val clickInfo = "• Клики (Click):\nТочечное нажатие по координатам с регулируемой задержкой, повторами и случайным разбросом.\n\n• Зажатие (Hold):\nУдержание точки на заданное время (в мс)."
        val swipeInfo = "• Свайпы (Swipe):\nПлавное перемещение от точки (S) к (E).\n\n• Траектория Джойстика:\nЗапись сложных свайпов через плавающий джойстик."
        val aiInfo = "• ИИ-Сканер (AI Trigger v40):\nПоиск заданного изображения на экране с калибровкой, выбором порога (%) и эстафетой сценариев."

        tvContent?.text = clickInfo

        tabClick?.setOnClickListener {
            tvContent?.text = clickInfo
            tabClick.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
        }

        tabSwipe?.setOnClickListener {
            tvContent?.text = swipeInfo
            tabClick?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
        }

        tabAi?.setOnClickListener {
            tvContent?.text = aiInfo
            tabClick?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabSwipe?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#0D1117"))
            tabAi?.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#58A6FF"))
        }

        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/MainActivity.kt", main_activity_code)

    print("✨ Все системные разрешения, отключение энергосбережения и Мастер-Инструкции v40.0.0 Enterprise успешно развернуты!")

if __name__ == "__main__":
    deploy_v40_ultimate_master()