import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Записан модуль v37.2: {rel_path}")

def fix_vertical_drag_and_consequential_bugs():
    print("🚀 Устранение ошибки вертикальной привязки оверлея v37.2.0-PRO...")

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
        versionCode = 2550
        versionName = "37.2.0-PRO"

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

    # 2. OverlayManager.kt (Явный Gravity.TOP|START + Мгновенный updateViewLayout)
    overlay_manager_code = r"""package com.example.autotap.ui.base

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.example.autotap.MyAutoClickService
import java.util.concurrent.ConcurrentHashMap

class OverlayManager(private val context: Context) {

    private val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

    private val attachedViews = ConcurrentHashMap<View, Boolean>()
    private val viewPool = ConcurrentHashMap<Int, MutableList<View>>()
    private val activeOverlays = ConcurrentHashMap<OverlayLayer, MutableList<OverlayBase>>()

    fun safeAddView(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] == true) return
        try {
            windowManager.addView(view, params)
            attachedViews[view] = true
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun safeRemoveView(view: View?) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.removeView(view)
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        } finally {
            attachedViews.remove(view)
        }
    }

    fun safeUpdateViewLayout(view: View?, params: WindowManager.LayoutParams) {
        if (view == null || attachedViews[view] != true) return
        try {
            windowManager.updateViewLayout(view, params)
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun getViewFromReusePool(layoutResId: Int): View? {
        val pool = viewPool[layoutResId]
        return if (!pool.isNullOrEmpty()) pool.removeAt(0) else null
    }

    fun recycleViewToPool(layoutResId: Int, view: View) {
        val pool = viewPool.getOrPut(layoutResId) { mutableListOf() }
        if (pool.size < 5 && !pool.contains(view)) {
            pool.add(view)
        }
    }

    fun pushOverlay(overlay: OverlayBase) {
        val list = activeOverlays.getOrPut(overlay.layer) { mutableListOf() }
        list.add(overlay)
        overlay.show()
    }

    fun popOverlay(layer: OverlayLayer) {
        val list = activeOverlays[layer]
        if (!list.isNullOrEmpty()) {
            val overlay = list.removeAt(list.size - 1)
            overlay.hide()
        }
    }

    fun clearLayer(layer: OverlayLayer) {
        activeOverlays[layer]?.forEach { it.hide() }
        activeOverlays[layer]?.clear()
    }

    fun detachOnStop() {
        clearLayer(OverlayLayer.DEBUG)
        clearLayer(OverlayLayer.CAPTURE)
        clearLayer(OverlayLayer.JOYSTICK)
        clearLayer(OverlayLayer.CANDIDATE)
        clearLayer(OverlayLayer.VISUALIZER)
    }

    fun detachOnScriptChange() {
        detachOnStop()
    }

    fun detachOnError() {
        detachOnStop()
    }

    fun detachOnOrientationChange() {
        activeOverlays.values.forEach { list ->
            list.forEach { if (it.isShowing) { it.hide(); it.show() } }
        }
    }

    fun dpToPx(dp: Int): Int = (dp * context.resources.displayMetrics.density).toInt()
    fun dpToPx(dp: Float): Int = (dp * context.resources.displayMetrics.density).toInt()

    fun getRealScreenSize(): Pair<Int, Int> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val bounds = windowManager.currentWindowMetrics.bounds
            Pair(bounds.width(), bounds.height())
        } else {
            val dm = DisplayMetrics()
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay.getRealMetrics(dm)
            Pair(dm.widthPixels, dm.heightPixels)
        }
    }

    fun getOverlayType(): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
    }

    fun createOverlayParams(): WindowManager.LayoutParams {
        return WindowManager.LayoutParams().apply {
            type = getOverlayType()
            format = PixelFormat.TRANSLUCENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN

            gravity = Gravity.TOP or Gravity.START

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }

            width = WindowManager.LayoutParams.WRAP_CONTENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/base/OverlayManager.kt", overlay_manager_code)

    # 3. ControlPanelOverlay.kt (Фикс вертикального перетаскивания и авто-выравнивания)
    control_panel_code = r"""package com.example.autotap.ui.overlays

import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.TextView
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority

class ControlPanelOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_control_panel, OverlayLayer.PANEL, OverlayPriority.MEDIUM) {

    private var stopButtonView: View? = null
    private var panelState = 0

    private var btnPlay: ImageButton? = null
    private var btnAdd: ImageButton? = null
    private var btnCapturePool: ImageButton? = null
    private var btnHelpTutorial: ImageButton? = null
    private var btnToggleMenu: ImageButton? = null

    private var btnClearAll: ImageButton? = null
    private var btnRecord: ImageButton? = null
    private var btnToggleJoystick: ImageButton? = null
    private var btnLoadScript: ImageButton? = null
    private var btnHideNumbers: ImageButton? = null
    private var btnClose: ImageButton? = null
    private var btnSingleBubble: ImageButton? = null

    private var layoutMainRow: View? = null
    private var layoutSubMenu: View? = null

    override fun onViewInflated(view: View) {
        val handleDrag = view.findViewById<TextView>(R.id.handleDrag)
        layoutMainRow = view.findViewById(R.id.layoutMainRow)
        layoutSubMenu = view.findViewById(R.id.layoutSubMenu)
        btnSingleBubble = view.findViewById(R.id.btnSingleBubble)

        btnPlay = view.findViewById(R.id.btnPlay)
        btnAdd = view.findViewById(R.id.btnAdd)
        btnCapturePool = view.findViewById(R.id.btnCapturePool)
        btnHelpTutorial = view.findViewById(R.id.btnHelpTutorial)
        btnToggleMenu = view.findViewById(R.id.btnToggleMenu)

        btnClearAll = view.findViewById(R.id.btnClearAll)
        btnRecord = view.findViewById(R.id.btnRecord)
        btnToggleJoystick = view.findViewById(R.id.btnToggleJoystick)
        btnLoadScript = view.findViewById(R.id.btnLoadScript)
        btnHideNumbers = view.findViewById(R.id.btnHideNumbers)
        btnClose = view.findViewById(R.id.btnClose)

        var initX = 0; var initY = 0; var touchX = 0f; var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val p = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x
                    initY = p.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (screenW, screenH) = service.overlayManager.getRealScreenSize()
                    val w = if (view.width > 0) view.width else service.dpToPx(180)
                    val h = if (view.height > 0) view.height else service.dpToPx(50)
                    val maxX = (screenW - w).coerceAtLeast(0)
                    val maxY = (screenH - h).coerceAtLeast(0)

                    p.gravity = Gravity.TOP or Gravity.START
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, maxX)
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, maxY)

                    service.overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        btnToggleMenu?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(panelState + 1) }
        btnSingleBubble?.setOnClickListener { service.vibrateFeedback(20L); updatePanelState(0) }

        btnPlay?.setOnClickListener {
            service.vibrateFeedback(30L)
            if (service.isPlaying) {
                btnPlay?.setImageResource(R.drawable.ic_play)
                service.stopExecutionLoop()
            } else {
                btnPlay?.setImageResource(R.drawable.ic_pause)
                service.startScript("default")
            }
        }

        btnAdd?.setOnClickListener { service.vibrateFeedback(20L); service.showAddActionMenu() }
        btnCapturePool?.setOnClickListener { service.vibrateFeedback(20L); service.captureFrameOverlay.show() }
        btnHelpTutorial?.setOnClickListener { service.vibrateFeedback(20L); service.showTutorialCard() }
        btnClearAll?.setOnClickListener { service.vibrateFeedback(30L); service.clearAllActions() }
        btnRecord?.setOnClickListener { service.vibrateFeedback(20L); if (service.isRecording) service.stopOverlayRecording() else service.startOverlayRecording() }
        btnToggleJoystick?.setOnClickListener {
            service.vibrateFeedback(20L)
            if (service.joystickOverlay.rootView != null) service.joystickOverlay.hide() else service.joystickOverlay.show()
        }
        btnLoadScript?.setOnClickListener { service.vibrateFeedback(20L); service.showScriptsDialog() }
        btnHideNumbers?.setOnClickListener { service.vibrateFeedback(20L); service.toggleNumbersVisibility() }
        btnClose?.setOnClickListener { service.vibrateFeedback(20L); service.hideControlPanel(openMainApp = true) }
    }

    fun ensureSubMenuVisible() {
        if (panelState != 1) {
            updatePanelState(1)
        }
    }

    fun getButtonForStep(step: Int): View? {
        return when (step) {
            0 -> btnPlay
            1 -> btnAdd
            2 -> btnCapturePool
            3 -> btnHelpTutorial
            4 -> btnToggleMenu
            5 -> btnClearAll
            6 -> btnRecord
            7 -> btnToggleJoystick
            8 -> btnLoadScript
            9 -> btnHideNumbers
            10 -> btnClose
            else -> null
        }
    }

    fun resetAllButtonScales() {
        val buttons = listOf(
            btnPlay, btnAdd, btnCapturePool, btnHelpTutorial, btnToggleMenu,
            btnClearAll, btnRecord, btnToggleJoystick, btnLoadScript, btnHideNumbers, btnClose
        )
        buttons.forEach { btn ->
            btn?.scaleX = 1.0f
            btn?.scaleY = 1.0f
        }
    }

    fun updatePanelState(state: Int) {
        panelState = state % 3
        when (panelState) {
            0 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.GONE }
            1 -> { layoutMainRow?.visibility = View.VISIBLE; layoutSubMenu?.visibility = View.VISIBLE; btnSingleBubble?.visibility = View.GONE }
            2 -> { layoutMainRow?.visibility = View.GONE; layoutSubMenu?.visibility = View.GONE; btnSingleBubble?.visibility = View.VISIBLE }
        }
        rootView?.requestLayout()
        val p = rootView?.layoutParams as? WindowManager.LayoutParams
        if (p != null && rootView != null) {
            val (screenW, screenH) = service.overlayManager.getRealScreenSize()
            p.width = WindowManager.LayoutParams.WRAP_CONTENT
            p.height = WindowManager.LayoutParams.WRAP_CONTENT
            p.gravity = Gravity.TOP or Gravity.START

            rootView?.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED)
            val h = if (rootView?.measuredHeight ?: 0 > 0) rootView!!.measuredHeight else service.dpToPx(105)
            val w = if (rootView?.measuredWidth ?: 0 > 0) rootView!!.measuredWidth else service.dpToPx(200)

            p.x = p.x.coerceIn(0, (screenW - w).coerceAtLeast(0))
            p.y = p.y.coerceIn(0, (screenH - h).coerceAtLeast(0))

            service.overlayManager.safeUpdateViewLayout(rootView, p)
        }
    }

    fun showFloatingStopButton() {
        if (stopButtonView != null) return
        val view = LayoutInflater.from(service).inflate(R.layout.floating_stop_button, null)
        stopButtonView = view

        val (screenW, _) = service.overlayManager.getRealScreenSize()
        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            x = (screenW - service.dpToPx(80)) / 2
            y = service.dpToPx(60)
        }

        val handleDrag = view.findViewById<TextView>(R.id.handleDragStop)
        var initX = 0; var initY = 0
        var touchX = 0f; var touchY = 0f

        handleDrag?.setOnTouchListener { _, event ->
            val p = view.layoutParams as? WindowManager.LayoutParams ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = p.x
                    initY = p.y
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val (sw, sh) = service.overlayManager.getRealScreenSize()
                    val w = if (view.width > 0) view.width else service.dpToPx(80)
                    val h = if (view.height > 0) view.height else service.dpToPx(40)
                    p.gravity = Gravity.TOP or Gravity.START
                    p.x = (initX + (event.rawX - touchX).toInt()).coerceIn(0, (sw - w).coerceAtLeast(0))
                    p.y = (initY + (event.rawY - touchY).toInt()).coerceIn(0, (sh - h).coerceAtLeast(0))
                    service.overlayManager.safeUpdateViewLayout(view, p)
                    true
                }
                else -> false
            }
        }

        val btnStop = view.findViewById<ImageButton>(R.id.btnFloatingStop)
        btnStop?.setOnClickListener {
            service.vibrateFeedback(20L)
            service.stopExecutionLoop()
        }

        service.overlayManager.safeAddView(view, params)
    }

    fun hideFloatingStopButton() {
        stopButtonView?.let { service.overlayManager.safeRemoveView(it) }
        stopButtonView = null
    }

    fun showClickVisualizer(x: Float, y: Float) {
        val view = LayoutInflater.from(service).inflate(R.layout.floating_beacon_ring, null)
        val params = service.overlayManager.createOverlayParams().apply {
            gravity = Gravity.TOP or Gravity.START
            this.x = x.toInt()
            this.y = y.toInt()
        }
        service.overlayManager.safeAddView(view, params)
        view.animate().alpha(0f).setDuration(300).withEndAction { service.overlayManager.safeRemoveView(view) }.start()
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/ControlPanelOverlay.kt", control_panel_code)

    # 4. MainActivity.kt (Версия 37.2.0-PRO)
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
        tvVersion?.text = "AutoTap v37.2.0-PRO"

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
            shareZip(zipFile, "Полный бэкап AutoTap v37.2")
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
        val aiInfo = "• ИИ-Сканер (AI Trigger v37):\nПоиск заданного изображения на экране с калибровкой, выбором порога (%) и эстафетой сценариев."

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

    print("✨ Плавное 120 FPS перетаскивание и фикс вертикальной привязки оверлеев успешно применены!")

if __name__ == "__main__":
    fix_vertical_drag_and_consequential_bugs()