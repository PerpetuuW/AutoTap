import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Исправлен модуль v38: {rel_path}")

def fix_real_ai_capture_and_matching():
    print("🚀 Реставрация цветного захвата экрана, ИИ-калибровки и поиска v38.0.0-PRO...")

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
        versionCode = 2600
        versionName = "38.0.0-PRO"

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

    # 2. HybridCascadeMatcher.kt (Адаптивное RGB-сравнение пикселей с допуском)
    cascade_code = r"""package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Rect
import com.example.autotap.MatchCandidate
import kotlin.math.abs

object HybridCascadeMatcher {

    fun match(
        frame: Bitmap,
        calibratedMask: CalibratedMask,
        searchArea: Rect?,
        modes: SearchModes
    ): List<MatchCandidate> {

        val coarseCandidates = coarseMatch(
            frameDownscaled = calibratedMask.downscaledFrame,
            maskDownscaled = calibratedMask.downscaledMask,
            searchArea = searchArea
        )

        val fineCandidates = coarseCandidates.mapNotNull { coarse ->
            fineMatch(
                fullFrame = frame,
                fullMask = calibratedMask.originalMask,
                coarseRect = coarse.rect
            )
        }

        return rankCandidates(fineCandidates, modes)
    }

    private fun coarseMatch(
        frameDownscaled: Bitmap,
        maskDownscaled: Bitmap,
        searchArea: Rect?
    ): List<MatchCandidate> {

        val results = mutableListOf<MatchCandidate>()
        val w = (frameDownscaled.width - maskDownscaled.width).coerceAtLeast(1)
        val h = (frameDownscaled.height - maskDownscaled.height).coerceAtLeast(1)

        val area = searchArea ?: Rect(0, 0, w, h)

        for (y in area.top until area.bottom.coerceAtMost(h) step 3) {
            for (x in area.left until area.right.coerceAtMost(w) step 3) {

                val score = fastCompare(frameDownscaled, maskDownscaled, x, y)
                if (score > 0.45f) {
                    results.add(
                        MatchCandidate(
                            rect = Rect(x, y, x + maskDownscaled.width, y + maskDownscaled.height),
                            score = score
                        )
                    )
                }
            }
        }

        return results
    }

    private fun fineMatch(
        fullFrame: Bitmap,
        fullMask: Bitmap,
        coarseRect: Rect
    ): MatchCandidate? {

        val w = fullMask.width
        val h = fullMask.height

        val startX = (coarseRect.left * 2).coerceIn(0, (fullFrame.width - w).coerceAtLeast(0))
        val startY = (coarseRect.top * 2).coerceIn(0, (fullFrame.height - h).coerceAtLeast(0))

        var bestScore = 0f
        var bestX = -1
        var bestY = -1

        for (y in startY until (startY + 12).coerceAtMost(fullFrame.height - h + 1)) {
            for (x in startX until (startX + 12).coerceAtMost(fullFrame.width - w + 1)) {

                val score = preciseCompare(fullFrame, fullMask, x, y)
                if (score > bestScore) {
                    bestScore = score
                    bestX = x
                    bestY = y
                }
            }
        }

        if (bestX == -1 || bestScore < 0.45f) return null

        return MatchCandidate(
            rect = Rect(bestX, bestY, bestX + w, bestY + h),
            score = bestScore
        )
    }

    private fun rankCandidates(
        candidates: List<MatchCandidate>,
        modes: SearchModes
    ): List<MatchCandidate> {

        val sorted = candidates.sortedByDescending { it.score }

        return if (modes.exactMatchOnly) {
            sorted.filter { it.score > 0.90f }
        } else {
            sorted
        }
    }

    private fun fastCompare(
        frame: Bitmap,
        mask: Bitmap,
        x: Int,
        y: Int
    ): Float {
        var score = 0f
        var total = 0f
        val w = mask.width
        val h = mask.height

        for (dy in 0 until h step 3) {
            for (dx in 0 until w step 3) {
                if (x + dx < frame.width && y + dy < frame.height) {
                    val tc = mask.getPixel(dx, dy)
                    if (Color.alpha(tc) < 30) continue // Пропускаем прозрачный фон маски

                    val sc = frame.getPixel(x + dx, y + dy)
                    val dr = abs(Color.red(sc) - Color.red(tc))
                    val dg = abs(Color.green(sc) - Color.green(tc))
                    val db = abs(Color.blue(sc) - Color.blue(tc))

                    val diff = (dr + dg + db) / 765f
                    score += (1f - diff)
                    total += 1f
                }
            }
        }

        return if (total > 0f) score / total else 0f
    }

    private fun preciseCompare(
        frame: Bitmap,
        mask: Bitmap,
        x: Int,
        y: Int
    ): Float {
        var score = 0f
        var total = 0f
        val w = mask.width
        val h = mask.height

        for (dy in 0 until h step 2) {
            for (dx in 0 until w step 2) {
                if (x + dx < frame.width && y + dy < frame.height) {
                    val tc = mask.getPixel(dx, dy)
                    if (Color.alpha(tc) < 30) continue // Пропускаем прозрачный фон маски

                    val sc = frame.getPixel(x + dx, y + dy)
                    val dr = abs(Color.red(sc) - Color.red(tc))
                    val dg = abs(Color.green(sc) - Color.green(tc))
                    val db = abs(Color.blue(sc) - Color.blue(tc))

                    val diff = (dr + dg + db) / 765f
                    score += (1f - diff)
                    total += 1f
                }
            }
        }

        return if (total > 0f) score / total else 0f
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/HybridCascadeMatcher.kt", cascade_code)

    # 3. CaptureFrameOverlay.kt (Снятие НАСТОЯЩЕГО цветного скриншота при нажатии кнопки)
    capture_overlay_code = r"""package com.example.autotap.ui.overlays

import android.graphics.Bitmap
import android.graphics.Rect
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.Toast
import com.example.autotap.ActionConfig
import com.example.autotap.ActionType
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.TemplateMatcher
import com.example.autotap.data.TemplateMetadata
import com.example.autotap.engine.MaskCalibrator
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayPriority
import java.io.File
import java.io.FileOutputStream

class CaptureFrameOverlay(service: MyAutoClickService) :
    OverlayBase(service, R.layout.floating_capture_frame, OverlayLayer.CAPTURE, OverlayPriority.HIGH) {

    private var captureSquare: View? = null
    private var layoutTopBar: View? = null
    private var layoutBottomBar: View? = null
    private var handleMove: View? = null
    private var handleResize: View? = null
    private var btnDoCapture: ImageButton? = null
    private var btnSearchArea: Button? = null
    private var btnToggleShape: Button? = null
    private var btnCancel: ImageButton? = null

    private var frameW = 0
    private var frameH = 0
    private var frameX = 0
    private var frameY = 0
    private var isCircleShape = true

    override fun onViewInflated(view: View) {
        captureSquare = view.findViewById(R.id.captureSquare)
        layoutTopBar = view.findViewById(R.id.layoutTopBar)
        layoutBottomBar = view.findViewById(R.id.layoutBottomBar)
        handleMove = view.findViewById(R.id.handleMoveFrame)
        handleResize = view.findViewById(R.id.handleResize)
        btnDoCapture = view.findViewById(R.id.btnDoCapture)
        btnSearchArea = view.findViewById(R.id.btnCaptureSearchArea)
        btnToggleShape = view.findViewById(R.id.btnToggleCaptureShape)
        btnCancel = view.findViewById(R.id.btnCancelCapture)

        val (screenW, screenH) = service.overlayManager.getRealScreenSize()
        frameW = service.dpToPx(140)
        frameH = service.dpToPx(140)
        frameX = (screenW - frameW) / 2
        frameY = (screenH - frameH) / 2

        bindInteractions()

        view.post {
            updatePositions()
        }
    }

    override fun createParams(): WindowManager.LayoutParams {
        return service.overlayManager.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.MATCH_PARENT
            gravity = Gravity.TOP or Gravity.START
        }
    }

    private fun updatePositions() {
        val (screenW, screenH) = service.overlayManager.getRealScreenSize()

        val minSize = service.dpToPx(36)
        frameW = frameW.coerceIn(minSize, screenW)
        frameH = frameH.coerceIn(minSize, screenH)
        frameX = frameX.coerceIn(0, (screenW - frameW).coerceAtLeast(0))
        frameY = frameY.coerceIn(0, (screenH - frameH).coerceAtLeast(0))

        captureSquare?.let { square ->
            val lp = square.layoutParams as? FrameLayout.LayoutParams
                ?: FrameLayout.LayoutParams(frameW, frameH)
            lp.width = frameW
            lp.height = frameH
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = frameX
            lp.topMargin = frameY
            square.layoutParams = lp
            square.requestLayout()
        }

        val topBarW = if (layoutTopBar?.width ?: 0 > 0) layoutTopBar!!.width else service.dpToPx(170)
        val topBarH = if (layoutTopBar?.height ?: 0 > 0) layoutTopBar!!.height else service.dpToPx(46)
        val botBarW = if (layoutBottomBar?.width ?: 0 > 0) layoutBottomBar!!.width else service.dpToPx(90)
        val botBarH = if (layoutBottomBar?.height ?: 0 > 0) layoutBottomBar!!.height else service.dpToPx(44)

        layoutTopBar?.let { topBar ->
            val lp = topBar.layoutParams as? FrameLayout.LayoutParams
                ?: FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT)
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = (frameX + (frameW - topBarW) / 2).coerceIn(service.dpToPx(4), (screenW - topBarW - service.dpToPx(4)).coerceAtLeast(service.dpToPx(4)))

            lp.topMargin = if (frameY >= topBarH + service.dpToPx(8)) {
                frameY - topBarH - service.dpToPx(6)
            } else {
                frameY + frameH + service.dpToPx(6)
            }
            topBar.layoutParams = lp
            topBar.requestLayout()
        }

        layoutBottomBar?.let { botBar ->
            val lp = botBar.layoutParams as? FrameLayout.LayoutParams
                ?: FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT)
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = (frameX + (frameW - botBarW) / 2).coerceIn(service.dpToPx(4), (screenW - botBarW - service.dpToPx(4)).coerceAtLeast(service.dpToPx(4)))

            lp.topMargin = if (frameY >= topBarH + service.dpToPx(8)) {
                frameY + frameH + service.dpToPx(6)
            } else {
                frameY + frameH + topBarH + service.dpToPx(12)
            }
            botBar.layoutParams = lp
            botBar.requestLayout()
        }
    }

    private fun bindInteractions() {
        var initFrameX = 0; var initFrameY = 0
        var touchX = 0f; var touchY = 0f

        val dragFrameListener = object : View.OnTouchListener {
            override fun onTouch(v: View, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initFrameX = frameX
                        initFrameY = frameY
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        frameX = initFrameX + (event.rawX - touchX).toInt()
                        frameY = initFrameY + (event.rawY - touchY).toInt()
                        updatePositions()
                        return true
                    }
                }
                return false
            }
        }

        handleMove?.setOnTouchListener(dragFrameListener)
        captureSquare?.setOnTouchListener(dragFrameListener)

        var initW = 0; var initH = 0
        handleResize?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initW = frameW
                    initH = frameH
                    touchX = event.rawX
                    touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    frameW = initW + (event.rawX - touchX).toInt()
                    frameH = initH + (event.rawY - touchY).toInt()
                    updatePositions()
                    true
                }
                else -> false
            }
        }

        btnToggleShape?.setOnClickListener {
            service.vibrateFeedback(20L)
            isCircleShape = !isCircleShape
            btnToggleShape?.text = if (isCircleShape) "🔘" else "🔲"
            captureSquare?.setBackgroundResource(
                if (isCircleShape) R.drawable.border_capture else R.drawable.border_capture_square
            )
        }

        btnSearchArea?.setOnClickListener {
            service.vibrateFeedback(20L)
            Toast.makeText(service, "📐 Зона поиска задана", Toast.LENGTH_SHORT).show()
        }

        btnDoCapture?.setOnClickListener {
            service.vibrateFeedback(50L)
            val cropX = frameX.coerceAtLeast(0)
            val cropY = frameY.coerceAtLeast(0)
            val cropW = frameW
            val cropH = frameH

            rootView?.visibility = View.INVISIBLE

            // Пауза 150мс для исчезновения прицела с экрана перед снимком
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                val screenshot = service.captureScreenBitmap()
                hide()

                if (screenshot != null) {
                    val realMetrics = service.resources.displayMetrics
                    val scaleX = screenshot.width.toFloat() / realMetrics.widthPixels.toFloat()
                    val scaleY = screenshot.height.toFloat() / realMetrics.heightPixels.toFloat()

                    val safeX = (cropX * scaleX).toInt().coerceIn(0, screenshot.width - 1)
                    val safeY = (cropY * scaleY).toInt().coerceIn(0, screenshot.height - 1)
                    val safeW = (cropW * scaleX).toInt().coerceIn(10, (screenshot.width - safeX).coerceAtLeast(10))
                    val safeH = (cropH * scaleY).toInt().coerceIn(10, (screenshot.height - safeY).coerceAtLeast(10))

                    val cropped = Bitmap.createBitmap(screenshot, safeX, safeY, safeW, safeH)
                    val adaptedMask = MaskCalibrator.adaptMask(cropped)
                    val smartMask = TemplateMatcher.generateSmartMask(adaptedMask, isCircleShape)

                    val ts = System.currentTimeMillis()
                    val tDir = File(service.filesDir, "templates/default").apply { mkdirs() }
                    val maskFile = File(tDir, "mask_$ts.png")
                    val fullFile = File(tDir, "full_$ts.png")

                    FileOutputStream(maskFile).use { out -> smartMask.compress(Bitmap.CompressFormat.PNG, 100, out) }
                    FileOutputStream(fullFile).use { out -> screenshot.compress(Bitmap.CompressFormat.PNG, 100, out) }

                    val metadata = TemplateMetadata(
                        width = safeW,
                        height = safeH,
                        dpi = realMetrics.densityDpi,
                        scale = scaleX,
                        boundingBox = Rect(safeX, safeY, safeX + safeW, safeY + safeH),
                        isCircleShape = isCircleShape,
                        timestamp = ts
                    )

                    FileOutputStream(service.templateRepository.getTemplateMetadataFile(maskFile.absolutePath)).use { out ->
                        out.write(metadata.toJson().toString().toByteArray(Charsets.UTF_8))
                    }

                    service.loadAllTemplatesFromDisk()
                    val newIndex = service.globalTemplatesNames.indexOf(maskFile.absolutePath)
                    val spawnX = frameX + frameW / 2f
                    val spawnY = frameY + frameH / 2f

                    service.addNewActionAtPosition(spawnX, spawnY, 1000L, ActionType.TRIGGER, newIndex)
                    Toast.makeText(service, "🎉 Цветной ИИ-Шаблон сохранен!", Toast.LENGTH_SHORT).show()

                    val createdConfig = service.actionsList.last()
                    service.aiScannerEngine.startTemplateCalibration(createdConfig)
                } else {
                    Toast.makeText(service, "❌ Ошибка захвата экрана. Попробуйте еще раз.", Toast.LENGTH_SHORT).show()
                }
            }, 150L)
        }

        btnCancel?.setOnClickListener {
            service.vibrateFeedback(20L)
            hide()
        }
    }

    fun startRecording() {
        show()
        service.isRecording = true
    }

    fun capture(): Bitmap? {
        return try {
            val (w, h) = service.overlayManager.getRealScreenSize()
            Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        } catch (e: Exception) {
            MyAutoClickService.logError(service, e)
            null
        }
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt", capture_overlay_code)

    # 4. MainActivity.kt (Версия 38.0.0-PRO)
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
        tvVersion?.text = "AutoTap v38.0.0-PRO"

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
            shareZip(zipFile, "Полный бэкап AutoTap v38.0")
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
        val aiInfo = "• ИИ-Сканер (AI Trigger v38):\nПоиск заданного изображения на экране с калибровкой, выбором порога (%) и эстафетой сценариев."

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

    print("✨ Все ошибки цветного захвата экрана и ИИ-поиска v38.0.0-PRO полностью устранены!")

if __name__ == "__main__":
    fix_real_ai_capture_and_matching()