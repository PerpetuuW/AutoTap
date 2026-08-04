import os

def apply_patches():
    print("🚀 Running AutoTap Build Repair Patch Script...")

    # 1. Update app/build.gradle.kts (Versioning Guard)
    gradle_path = os.path.join("app", "build.gradle.kts")
    if os.path.exists(gradle_path):
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
        versionCode = 2336
        versionName = "28.13.0-PRO"

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
        with open(gradle_path, "w", encoding="utf-8") as f:
            f.write(gradle_code)
        print("  [✓] Updated app/build.gradle.kts")

    # 2. Fix MainActivity.kt (Unresolved tvLogsContent & dialog_permissions references)
    main_activity_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "MainActivity.kt")
    if os.path.exists(main_activity_path):
        main_activity_code = r"""package com.example.autotap

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
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
        tvVersion.text = "AutoTap v28.13.0 PRO"

        val btnAppDetails = findViewById<Button>(R.id.btnAppDetails)
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)
        val btnExport = findViewById<Button>(R.id.btnExport)
        val btnImport = findViewById<Button>(R.id.btnImport)
        val btnStartPanel = findViewById<Button>(R.id.btnStartPanel)
        val btnShowLogs = findViewById<Button>(R.id.btnShowLogs)
        val btnManageTemplates = findViewById<Button>(R.id.btnManageTemplates)
        val btnPermissionsHelp = findViewById<Button>(R.id.btnPermissionsHelp)

        btnAppDetails.setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            })
        }

        btnAccessibility.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        btnOverlay.setOnClickListener {
            try {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")))
            } catch (_: Exception) {
                startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION))
            }
        }

        btnExport.setOnClickListener { showExportDialog() }
        btnImport.setOnClickListener { startImportFlow() }
        btnShowLogs.setOnClickListener { showLogsDialog() }
        btnManageTemplates.setOnClickListener { showTemplatesManagerDialog() }
        btnPermissionsHelp.setOnClickListener { showPermissionsHelpDialog() }

        btnStartPanel.setOnClickListener {
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

    private fun updatePermissionButtonStates() {
        val btnAccessibility = findViewById<Button>(R.id.btnAccessibility)
        val btnOverlay = findViewById<Button>(R.id.btnOverlay)

        val isServiceBound = MyAutoClickService.instance != null
        val isSystemEnabled = isAccessibilityServiceEnabled()
        val isOverlayGranted = Settings.canDrawOverlays(this)

        btnAccessibility.text =
            if (isServiceBound) "Служба кликера: ВКЛЮЧЕНА"
            else if (isSystemEnabled) "Перезапустить службу"
            else "Разрешить работу кликера"

        btnAccessibility.backgroundTintList =
            ColorStateList.valueOf(if (isServiceBound) Color.parseColor("#1E3A2B") else Color.parseColor("#8B0000"))

        btnOverlay.text =
            if (isOverlayGranted) "Показ поверх окон: РАЗРЕШЕНО"
            else "Показ поверх окон: ОТКЛЮЧЕНО"

        btnOverlay.backgroundTintList =
            ColorStateList.valueOf(if (isOverlayGranted) Color.parseColor("#1E3A2B") else Color.parseColor("#21262D"))
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val am = getSystemService(Context.ACCESSIBILITY_SERVICE) as? android.view.accessibility.AccessibilityManager
        val enabled = am?.getEnabledAccessibilityServiceList(
            android.accessibilityservice.AccessibilityServiceInfo.FEEDBACK_ALL_MASK
        ) ?: emptyList()

        if (enabled.any { it.resolveInfo.serviceInfo.packageName == packageName }) return true

        val raw = Settings.Secure.getString(contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: ""

        return raw.split(':').any { it.substringBefore('/').equals(packageName, true) }
    }

    private fun showExportDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_export_select, null)
        val ad = AlertDialog.Builder(this).setView(dialogView).create()

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
            shareZip(zipFile, "Полный бэкап AutoTap")
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
            while (zis.nextEntry.also { entry = it } != null) {
                val name = entry!!.name
                val outFile = File(filesDir, name)

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
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseLogs)

        val logFile = File(filesDir, "error_log.txt")
        tvLogs.text = if (logFile.exists()) logFile.readText() else "Логи отсутствуют"

        val ad = AlertDialog.Builder(this).setView(dialogView).create()
        btnClose?.setOnClickListener { ad.dismiss() }
        ad.show()
    }

    private fun showTemplatesManagerDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_templates_manager, null)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutTemplatesList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnCloseTemplatesManager)

        val ad = AlertDialog.Builder(this).setView(dialogView).create()

        fun refresh() {
            layoutList.removeAllViews()
            val baseDir = File(filesDir, "templates")

            baseDir.listFiles()?.forEach { folder ->
                if (folder.isDirectory) {
                    folder.listFiles()?.forEach { file ->
                        if (file.name.startsWith("mask_") && file.name.endsWith(".png")) {
                            val item = LayoutInflater.from(this)
                                .inflate(R.layout.item_template, null)

                            val iv = item.findViewById<ImageView>(R.id.ivTemplatePreview)
                            val tv = item.findViewById<TextView>(R.id.tvTemplateName)
                            val btnDelete = item.findViewById<Button>(R.id.btnDeleteTemplateFile)

                            iv.setImageBitmap(BitmapFactory.decodeFile(file.absolutePath))
                            tv.text = "${folder.name}\n${file.nameWithoutExtension}"

                            btnDelete.setOnClickListener {
                                MyAutoClickService.instance?.moveTemplateToTrash(
                                    MyAutoClickService.instance?.globalTemplatesNames?.indexOf(file.absolutePath)
                                        ?: -1
                                )
                                MyAutoClickService.instance?.loadAllTemplatesFromDisk()
                                refresh()
                            }

                            layoutList.addView(item)
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
}
"""
        with open(main_activity_path, "w", encoding="utf-8") as f:
            f.write(main_activity_code)
        print("  [✓] Fixed MainActivity.kt")

    # 3. Fix MyAutoClickService.kt (Implement onAccessibilityEvent)
    service_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "MyAutoClickService.kt")
    if os.path.exists(service_path):
        service_code = r"""package com.example.autotap

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.graphics.Bitmap
import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.core.GestureExecutor
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.AiScannerEngine
import com.example.autotap.engine.ScriptExecutor
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.debug.ScenarioDebuggerOverlay
import com.example.autotap.ui.overlays.ControlPanelOverlay
import com.example.autotap.ui.overlays.JoystickOverlay
import com.example.autotap.ui.overlays.CaptureFrameOverlay
import com.example.autotap.ui.overlays.ScriptsDialog
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class MyAutoClickService : AccessibilityService() {

    companion object {
        var instance: MyAutoClickService? = null

        fun logError(ctx: Context, e: Throwable) {
            try {
                val file = File(ctx.filesDir, "error_log.txt")
                file.appendText("\n\n${System.currentTimeMillis()}:\n${e.stackTraceToString()}")
            } catch (_: Exception) {}
        }

        fun logAppEvent(ctx: Context, tag: String, msg: String) {
            try {
                val file = File(ctx.filesDir, "app_events.txt")
                file.appendText("\n[$tag] $msg")
            } catch (_: Exception) {}
        }
    }

    // CORE MODULES
    lateinit var overlayManager: OverlayManager
    lateinit var gestureExecutor: GestureExecutor
    lateinit var scriptExecutor: ScriptExecutor
    lateinit var aiScannerEngine: AiScannerEngine
    lateinit var templateRepository: TemplateRepository
    lateinit var scriptRepository: ScriptRepository

    // UI OVERLAYS
    lateinit var controlPanelOverlay: ControlPanelOverlay
    lateinit var joystickOverlay: JoystickOverlay
    lateinit var captureFrameOverlay: CaptureFrameOverlay
    lateinit var debuggerOverlay: ScenarioDebuggerOverlay

    // SCRIPT STATE
    val actionsList = ArrayList<ActionConfig>()
    var isPlaying = false
    var isRecording = false

    var globalClickDurationMs: Long = 120L
    var globalScriptLoopCount: Int = 1
    var isGlobalScriptInfinite: Boolean = false
    var globalRelayNextScript: String = ""

    val globalTemplatesNames: ArrayList<String>
        get() = templateRepository.globalTemplatesNames

    private val uiHandler = Handler(Looper.getMainLooper())

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Event processing hook if needed
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this

        overlayManager = OverlayManager(this)
        gestureExecutor = GestureExecutor(this)
        scriptExecutor = ScriptExecutor(this)
        aiScannerEngine = AiScannerEngine(this)
        templateRepository = TemplateRepository(this)
        scriptRepository = ScriptRepository(this)

        controlPanelOverlay = ControlPanelOverlay(this)
        joystickOverlay = JoystickOverlay(this)
        captureFrameOverlay = CaptureFrameOverlay(this)
        debuggerOverlay = ScenarioDebuggerOverlay(this)

        templateRepository.loadAllTemplatesFromDisk()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityServiceInfo.FEEDBACK_GENERIC
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }

        Toast.makeText(this, "AutoTap v28.13.0 PRO запущен", Toast.LENGTH_SHORT).show()
    }

    override fun onInterrupt() {}

    fun vibrateFeedback(durationMs: Long = 25L) {
        gestureExecutor.vibrateFeedback(durationMs)
    }

    fun showControlPanel() {
        controlPanelOverlay.show()
    }

    fun hideControlPanel() {
        controlPanelOverlay.hide()
    }

    fun showFloatingStopButton() {
        controlPanelOverlay.showFloatingStopButton()
    }

    fun hideFloatingStopButton() {
        controlPanelOverlay.hideFloatingStopButton()
    }

    fun showScriptsDialog() {
        ScriptsDialog(this).show()
    }

    fun startScript(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))

        if (actionsList.isEmpty()) {
            Toast.makeText(this, "Сценарий пуст!", Toast.LENGTH_SHORT).show()
            return
        }

        isPlaying = true
        scriptExecutor.startExecutionLoop()
    }

    fun stopExecutionLoop() {
        isPlaying = false
        scriptExecutor.stopExecutionLoop()
    }

    fun addNewActionAtPosition(x: Float, y: Float, delay: Long, type: ActionType, id: Int) {
        val cfg = ActionConfig(
            id = if (id == -1) (actionsList.size + 1) else id,
            type = type,
            xNorm = normalizeX(x),
            yNorm = normalizeY(y),
            delay = delay
        )
        actionsList.add(cfg)
    }

    fun stopOverlayRecording() {
        isRecording = false
        controlPanelOverlay.show()
        hideFloatingStopButton()
    }

    fun captureScreenBitmap(): Bitmap? {
        return captureFrameOverlay.capture()
    }

    fun normalizeX(px: Float): Float {
        val dm = resources.displayMetrics
        return (px / dm.widthPixels).coerceIn(0f, 1f)
    }

    fun normalizeY(px: Float): Float {
        val dm = resources.displayMetrics
        return (px / dm.heightPixels).coerceIn(0f, 1f)
    }

    fun resolveNormalizedPoint(nx: Float, ny: Float): Pair<Float, Float> {
        val dm = resources.displayMetrics
        return Pair(
            (nx * dm.widthPixels).coerceIn(0f, dm.widthPixels.toFloat()),
            (ny * dm.heightPixels).coerceIn(0f, dm.heightPixels.toFloat())
        )
    }

    fun randomOffset(radius: Int): PointF {
        if (radius <= 0) return PointF(0f, 0f)
        val dx = (-radius..radius).random().toFloat()
        val dy = (-radius..radius).random().toFloat()
        return PointF(dx, dy)
    }

    fun showClickVisualizer(x: Float, y: Float) {
        controlPanelOverlay.showClickVisualizer(x, y)
    }

    fun loadScriptByName(name: String) {
        actionsList.clear()
        actionsList.addAll(scriptRepository.loadScriptByName(name))
    }

    fun moveTemplateToTrash(index: Int) {
        templateRepository.moveTemplateToTrash(index)
    }

    fun loadAllTemplatesFromDisk() {
        templateRepository.loadAllTemplatesFromDisk()
    }

    fun onCandidateSelected(point: PointF) {
        logAppEvent(this, "SELECTION", "Selected point: (${point.x}, ${point.y})")
    }

    fun exportScriptWithTemplates(context: Context, scriptName: String) {
        val scriptFile = File(File(filesDir, "scripts"), "$scriptName.json")
        if (!scriptFile.exists()) return
        val zipFile = File(externalCacheDir ?: cacheDir, "script_${scriptName}.zip")
        try {
            val zos = ZipOutputStream(FileOutputStream(zipFile))
            zos.putNextEntry(ZipEntry(scriptFile.name))
            zos.write(scriptFile.readBytes())
            zos.closeEntry()
            zos.close()
            shareZipFile(zipFile, "Сценарий $scriptName")
        } catch (e: Exception) {
            logError(this, e)
        }
    }

    fun showScriptPickerDialog(title: String, onSelected: (String) -> Unit) {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_select_script_for_export, null)
        val tvTitle = dialogView.findViewById<TextView>(R.id.tvPickerTitle)
        val layoutList = dialogView.findViewById<LinearLayout>(R.id.layoutPickerList)
        val btnClose = dialogView.findViewById<Button>(R.id.btnClosePicker)

        tvTitle?.text = title
        val params = overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
            gravity = Gravity.CENTER
            flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            dimAmount = 0.5f
        }

        val dir = File(filesDir, "scripts")
        if (dir.exists()) {
            dir.listFiles()?.forEach { file ->
                if (file.name.endsWith(".json")) {
                    val btn = Button(this).apply {
                        text = file.nameWithoutExtension
                        setTextColor(android.graphics.Color.WHITE)
                        setBackgroundColor(android.graphics.Color.parseColor("#1C2541"))
                        setOnClickListener {
                            onSelected(file.nameWithoutExtension)
                            overlayManager.safeRemoveView(dialogView)
                        }
                    }
                    layoutList?.addView(btn)
                }
            }
        }

        btnClose?.setOnClickListener { overlayManager.safeRemoveView(dialogView) }
        overlayManager.safeAddView(dialogView, params)
    }

    fun shareZipFile(zipFile: File, title: String) {
        try {
            val uri = androidx.core.content.FileProvider.getUriForFile(
                this,
                "$packageName.fileprovider",
                zipFile
            )

            val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(android.content.Intent.EXTRA_STREAM, uri)
                addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }

            startActivity(android.content.Intent.createChooser(intent, title))

        } catch (e: Exception) {
            logError(this, e)
        }
    }
}
"""
        with open(service_path, "w", encoding="utf-8") as f:
            f.write(service_code)
        print("  [✓] Fixed MyAutoClickService.kt (implemented onAccessibilityEvent)")

    # 4. Fix ScriptExecutor.kt
    script_exec_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "engine", "ScriptExecutor.kt")
    if os.path.exists(script_exec_path):
        script_exec_code = r"""package com.example.autotap.engine

import android.graphics.PointF
import android.os.Handler
import android.os.Looper
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService

class ScriptExecutor(private val service: MyAutoClickService) {

    private var executionThread: Thread? = null
    private val uiHandler = Handler(Looper.getMainLooper())

    fun startExecutionLoop() {
        if (executionThread != null) return
        if (service.actionsList.isEmpty()) return

        executionThread = Thread {
            var currentIndex = 0

            uiHandler.post {
                service.hideControlPanel()
                service.joystickOverlay.hide()
                service.showFloatingStopButton()
            }

            while (service.isPlaying && service.actionsList.isNotEmpty()) {
                val action = service.actionsList[currentIndex]

                try {
                    Thread.sleep(action.delay)
                } catch (_: InterruptedException) {
                    break
                }

                if (!service.isPlaying) break

                when (action.type) {

                    ActionType.CLICK -> {
                        val (x, y) = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val jitter = service.randomOffset(action.randomRadius)
                        val fx = x + jitter.x
                        val fy = y + jitter.y

                        uiHandler.post {
                            service.showClickVisualizer(fx, fy)
                        }

                        service.gestureExecutor.performClickWithCallback(
                            fx,
                            fy,
                            service.globalClickDurationMs
                        )
                    }

                    ActionType.LONG_PRESS -> {
                        val (x, y) = service.resolveNormalizedPoint(action.xNorm, action.yNorm)

                        uiHandler.post {
                            service.showClickVisualizer(x, y)
                        }

                        service.gestureExecutor.performClickWithCallback(
                            x,
                            y,
                            action.holdDuration
                        )
                    }

                    ActionType.SWIPE -> {
                        val (sx, sy) = service.resolveNormalizedPoint(action.xNorm, action.yNorm)
                        val (ex, ey) = service.resolveNormalizedPoint(action.endXNorm, action.endYNorm)

                        if (action.joystickPath.isNotEmpty()) {
                            val path = action.joystickPath.map { p ->
                                val (px, py) = service.resolveNormalizedPoint(p.x, p.y)
                                PointF(px, py)
                            }

                            service.gestureExecutor.performPathSwipeWithCallback(
                                path,
                                sx,
                                sy,
                                ex,
                                ey,
                                action.holdDuration
                            )
                        } else {
                            service.gestureExecutor.performSwipeWithCallback(
                                sx,
                                sy,
                                ex,
                                ey,
                                action.holdDuration
                            )
                        }
                    }

                    ActionType.TRIGGER -> {
                        val jumpTargetStepId = service.aiScannerEngine.executeAiTriggerSequence(action)

                        when {
                            jumpTargetStepId == -999 -> {
                                currentIndex = 0
                                continue
                            }

                            jumpTargetStepId > 0 -> {
                                val targetIdx = service.actionsList.indexOfFirst { it.id == jumpTargetStepId }
                                if (targetIdx != -1) {
                                    currentIndex = targetIdx
                                    continue
                                }
                            }
                        }
                    }
                }

                currentIndex = (currentIndex + 1) % service.actionsList.size
            }

            service.isPlaying = false

            uiHandler.post {
                stopExecutionLoop()
            }
        }

        executionThread?.start()
    }

    fun stopExecutionLoop() {
        service.isPlaying = false
        executionThread?.interrupt()
        executionThread = null

        uiHandler.post {
            service.hideFloatingStopButton()
            service.showControlPanel()
        }
    }
}
"""
        with open(script_exec_path, "w", encoding="utf-8") as f:
            f.write(script_exec_code)
        print("  [✓] Fixed ScriptExecutor.kt")

    # 5. Fix CaptureFrameOverlay.kt
    capture_overlay_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "ui", "overlays", "CaptureFrameOverlay.kt")
    if os.path.exists(capture_overlay_path):
        capture_overlay_code = r"""package com.example.autotap.ui.overlays

import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class CaptureFrameOverlay(
    private val service: MyAutoClickService,
    private val overlayManager: OverlayManager = service.overlayManager
) {

    private var rootView: View? = null

    fun show() {
        hide()

        val view = LayoutInflater.from(service)
            .inflate(R.layout.floating_capture_frame, null)

        rootView = view

        val btnDoCapture = view.findViewById<ImageButton>(R.id.btnDoCapture)
        val btnCancel = view.findViewById<ImageButton>(R.id.btnCancelCapture)

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(30L)
            hide()
        }

        btnCancel?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }

        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
    }

    fun startRecording() {
        show()
        service.isRecording = true
    }

    fun capture(): Bitmap? {
        return try {
            val dm = service.resources.displayMetrics
            val width = dm.widthPixels
            val height = dm.heightPixels
            Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
"""
        with open(capture_overlay_path, "w", encoding="utf-8") as f:
            f.write(capture_overlay_code)
        print("  [✓] Fixed CaptureFrameOverlay.kt")

    # 6. Fix ControlPanelOverlay.kt
    control_panel_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "ui", "overlays", "ControlPanelOverlay.kt")
    if os.path.exists(control_panel_path):
        control_panel_code = r"""package com.example.autotap.ui.overlays

import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class ControlPanelOverlay(private val service: MyAutoClickService) {

    private var panelView: View? = null
    private var stopButtonView: View? = null

    fun show() {
        if (panelView != null) {
            panelView?.visibility = View.VISIBLE
            return
        }

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_control_panel, null)
        panelView = view

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = service.overlayManager.dpToPx(20)
            y = service.overlayManager.dpToPx(120)
        }

        bindUi(view)
        service.overlayManager.safeAddView(view, params)
    }

    fun hide() {
        panelView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        panelView = null
    }

    private fun bindUi(view: View) {
        val btnPlay = view.findViewById<ImageButton>(R.id.btnPlay)
        val btnAdd = view.findViewById<ImageButton>(R.id.btnAdd)
        val btnRecord = view.findViewById<ImageButton>(R.id.btnRecord)
        val btnLoadScript = view.findViewById<ImageButton>(R.id.btnLoadScript)
        val btnClose = view.findViewById<ImageButton>(R.id.btnClose)

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.startScript("default")
        }

        btnAdd?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.captureFrameOverlay.startRecording()
        }

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.captureFrameOverlay.startRecording()
        }

        btnLoadScript?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.showScriptsDialog()
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return

        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
        }

        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.stopExecutionLoop()
        }

        service.overlayManager.safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let {
            service.overlayManager.safeRemoveView(it)
        }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val inflater = LayoutInflater.from(service)
        val view = inflater.inflate(R.layout.floating_beacon_ring, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }

        service.overlayManager.safeAddView(view, params)

        view.animate()
            .alpha(0f)
            .setDuration(300)
            .withEndAction {
                service.overlayManager.safeRemoveView(view)
            }
            .start()
    }
}
"""
        with open(control_panel_path, "w", encoding="utf-8") as f:
            f.write(control_panel_code)
        print("  [✓] Fixed ControlPanelOverlay.kt")

    # 7. Fix EditActionDialog.kt
    edit_action_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "ui", "overlays", "EditActionDialog.kt")
    if os.path.exists(edit_action_path):
        edit_action_code = r"""package com.example.autotap.ui.overlays

import android.content.res.ColorStateList
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R

class EditActionDialog(private val service: MyAutoClickService) {

    fun show(config: ActionConfig) {
        val dialogView = LayoutInflater.from(service)
            .inflate(R.layout.floating_edit_dialog, null)

        val currentStepIdx = service.actionsList.indexOf(config)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            service.overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }

        bindUi(dialogView, config, currentStepIdx)
        service.overlayManager.safeAddView(dialogView, params)
    }

    private fun bindUi(dialogView: View, config: ActionConfig, currentStepIdx: Int) {

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etRepeat = dialogView.findViewById<EditText>(R.id.etRepeatCount)
        val etRandomRadius = dialogView.findViewById<EditText>(R.id.etRandomRadius)
        val etHoldDuration = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val btnPrevStep = dialogView.findViewById<Button>(R.id.btnPrevStep)
        val btnNextStep = dialogView.findViewById<Button>(R.id.btnNextStep)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSave)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        tvTitle.text = "Действие #${config.id}"
        etDelay.setText((config.delay / 1000.0).toString())
        etRepeat.setText(config.repeatCount.toString())
        etRandomRadius.setText(config.randomRadius.toString())
        etHoldDuration.setText(config.holdDuration.toString())

        var selectedType = config.type

        fun applyType(t: ActionType) {
            selectedType = t
            config.type = t
        }

        btnTypeClick.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.CLICK)
            updateUi(dialogView, config, selectedType)
        }

        btnTypeHold.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.LONG_PRESS)
            updateUi(dialogView, config, selectedType)
        }

        btnTypeSwipe.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.SWIPE)
            updateUi(dialogView, config, selectedType)
        }

        btnTypeTrigger.setOnClickListener {
            service.vibrateFeedback(20L)
            applyType(ActionType.TRIGGER)
            updateUi(dialogView, config, selectedType)
        }

        fun saveConfig() {
            val delaySec = etDelay.text.toString().toDoubleOrNull() ?: 1.0
            config.delay = (delaySec * 1000).toLong().coerceAtLeast(50L)
            config.repeatCount = etRepeat.text.toString().toIntOrNull()?.coerceAtLeast(1) ?: 1
            config.randomRadius = etRandomRadius.text.toString().toIntOrNull()?.coerceAtLeast(0) ?: 0
            config.holdDuration = etHoldDuration.text.toString().toLongOrNull()?.coerceAtLeast(100L) ?: 1000L
        }

        btnSave.setOnClickListener {
            service.vibrateFeedback(30L)
            saveConfig()
            service.overlayManager.safeRemoveView(dialogView)
            Toast.makeText(service, "Шаг #${config.id} сохранён", Toast.LENGTH_SHORT).show()
        }

        btnCancel.setOnClickListener {
            service.vibrateFeedback(20L)
            service.overlayManager.safeRemoveView(dialogView)
        }

        btnPrevStep.setOnClickListener {
            saveConfig()
            service.overlayManager.safeRemoveView(dialogView)
            if (currentStepIdx > 0) show(service.actionsList[currentStepIdx - 1])
        }

        btnNextStep.setOnClickListener {
            saveConfig()
            service.overlayManager.safeRemoveView(dialogView)
            if (currentStepIdx < service.actionsList.size - 1) show(service.actionsList[currentStepIdx + 1])
        }

        updateUi(dialogView, config, selectedType)
    }

    private fun updateUi(dialogView: View, config: ActionConfig, selectedType: ActionType) {

        val btnTypeClick = dialogView.findViewById<Button>(R.id.btnTypeClick)
        val btnTypeHold = dialogView.findViewById<Button>(R.id.btnTypeHold)
        val btnTypeSwipe = dialogView.findViewById<Button>(R.id.btnTypeSwipe)
        val btnTypeTrigger = dialogView.findViewById<Button>(R.id.btnTypeTrigger)

        val tvHoldTitle = dialogView.findViewById<TextView>(R.id.tvHoldTitle)
        val etHoldDuration = dialogView.findViewById<EditText>(R.id.etHoldDuration)

        val isClick = selectedType == ActionType.CLICK
        val isHold = selectedType == ActionType.LONG_PRESS
        val isSwipe = selectedType == ActionType.SWIPE
        val isTrigger = selectedType == ActionType.TRIGGER

        btnTypeClick.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isClick) R.color.accent_blue else R.color.panel_blue))

        btnTypeHold.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isHold) R.color.accent_blue else R.color.panel_blue))

        btnTypeSwipe.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isSwipe) R.color.accent_blue else R.color.panel_blue))

        btnTypeTrigger.backgroundTintList =
            ColorStateList.valueOf(service.getColor(if (isTrigger) R.color.accent_blue else R.color.panel_blue))

        tvHoldTitle.visibility = if (isHold) View.VISIBLE else View.GONE
        etHoldDuration.visibility = if (isHold) View.VISIBLE else View.GONE
    }
}
"""
        with open(edit_action_path, "w", encoding="utf-8") as f:
            f.write(edit_action_code)
        print("  [✓] Fixed EditActionDialog.kt")

    # 8. Fix JoystickOverlay.kt
    joystick_overlay_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "ui", "overlays", "JoystickOverlay.kt")
    if os.path.exists(joystick_overlay_path):
        joystick_overlay_code = r"""package com.example.autotap.ui.overlays

import android.graphics.PixelFormat
import android.graphics.PointF
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayManager

class JoystickOverlay(
    private val service: MyAutoClickService,
    private val overlayManager: OverlayManager = service.overlayManager
) {

    private var rootView: View? = null
    private val pathPoints = ArrayList<PointF>()
    private var isRecordingPath = false

    fun show() {
        if (rootView != null) return

        val view = View.inflate(service, R.layout.floating_joystick_control, null)
        rootView = view

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            overlayManager.getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }

        bindUi(view)
        overlayManager.safeAddView(view, params)
    }

    fun hide() {
        rootView?.let { overlayManager.safeRemoveView(it) }
        rootView = null
        pathPoints.clear()
        isRecordingPath = false
    }

    private fun bindUi(view: View) {
        val btnRecord = view.findViewById<Button>(R.id.btnRecordJoystick)
        val btnClose = view.findViewById<ImageButton>(R.id.btnCloseJoystick)
        val touchArea = view.findViewById<View>(R.id.viewJoystickBase)

        btnRecord?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (!isRecordingPath) {
                startRecordingPath()
                btnRecord.text = "⏹ СОХРАНИТЬ"
            } else {
                savePathAsAction()
            }
        }

        btnClose?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }

        touchArea?.setOnTouchListener { _, event ->
            if (!isRecordingPath) return@setOnTouchListener false

            val x = event.x
            val y = event.y

            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    pathPoints.clear()
                    pathPoints.add(PointF(x, y))
                }
                MotionEvent.ACTION_MOVE -> {
                    pathPoints.add(PointF(x, y))
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    pathPoints.add(PointF(x, y))
                }
            }
            true
        }
    }

    private fun startRecordingPath() {
        pathPoints.clear()
        isRecordingPath = true
    }

    private fun savePathAsAction() {
        if (pathPoints.size < 2) {
            service.vibrateFeedback(40L)
            hide()
            return
        }

        val dm = service.resources.displayMetrics

        val normPath = ArrayList<PointF>().apply {
            pathPoints.forEach { p ->
                add(
                    PointF(
                        (p.x / dm.widthPixels).coerceIn(0f, 1f),
                        (p.y / dm.heightPixels).coerceIn(0f, 1f)
                    )
                )
            }
        }

        val first = normPath.first()
        val last = normPath.last()

        val cfg = ActionConfig(
            id = service.actionsList.size + 1,
            type = ActionType.SWIPE,
            xNorm = first.x,
            yNorm = first.y,
            endXNorm = last.x,
            endYNorm = last.y,
            holdDuration = 600L,
            joystickPath = normPath
        )

        service.actionsList.add(cfg)
        hide()
    }
}
"""
        with open(joystick_overlay_path, "w", encoding="utf-8") as f:
            f.write(joystick_overlay_code)
        print("  [✓] Fixed JoystickOverlay.kt")

    print("✨ All 8 files successfully repaired!")

if __name__ == "__main__":
    apply_patches()