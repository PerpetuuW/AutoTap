import os

def apply_template_matcher_repair():
    print("🚀 Исправление ошибок TemplateMatcher и TemplateRepository v28.16.0 PRO...")

    # 1. Обновление app/build.gradle.kts
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
        versionCode = 2339
        versionName = "28.16.0-PRO"

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
        print("  [✓] Обновлен app/build.gradle.kts (versionCode=2339, versionName=28.16.0-PRO)")

    # 2. Обновление TemplateMatcher.kt (Добавлена функция aggregateMultiFrameMask)
    template_matcher_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "TemplateMatcher.kt")
    if os.path.exists(template_matcher_path):
        template_matcher_code = r"""package com.example.autotap

import android.graphics.*
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

data class MatchCandidate(
    val rect: Rect,
    val score: Float,
    val templateIndex: Int = -1
) {
    val point: PointF
        get() = PointF(rect.centerX().toFloat(), rect.centerY().toFloat())
}

object TemplateMatcher {

    fun analyzeTemplate(template: Bitmap): JSONObject {
        return JSONObject().apply {
            put("width", template.width)
            put("height", template.height)
        }
    }

    fun generateSmartMask(src: Bitmap, isCircle: Boolean): Bitmap {
        val out = src.copy(Bitmap.Config.ARGB_8888, true)
        if (isCircle) {
            applyCircularMask(out)
        }
        return out
    }

    fun aggregateMultiFrameMask(frames: List<Bitmap>, circleShape: Boolean): Bitmap {
        if (frames.isEmpty()) return Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)

        val w = frames[0].width
        val h = frames[0].height

        val out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)

        for (y in 0 until h) {
            for (x in 0 until w) {

                var sumR = 0
                var sumG = 0
                var sumB = 0
                var sumA = 0

                for (bmp in frames) {
                    val c = bmp.getPixel(x, y)
                    sumR += Color.red(c)
                    sumG += Color.green(c)
                    sumB += Color.blue(c)
                    sumA += Color.alpha(c)
                }

                val avgR = sumR / frames.size
                val avgG = sumG / frames.size
                val avgB = sumB / frames.size
                val avgA = sumA / frames.size

                val finalColor = Color.argb(avgA, avgR, avgG, avgB)
                out.setPixel(x, y, finalColor)
            }
        }

        if (circleShape) {
            applyCircularMask(out)
        }

        return out
    }

    fun findCandidatesForCreation(screenBitmap: Bitmap, template: Bitmap): MutableList<MatchCandidate> {
        val list = ArrayList<MatchCandidate>()
        list.add(MatchCandidate(Rect(0, 0, template.width, template.height), 1.0f))
        return list
    }

    fun findTemplateCandidatesCoarseFine(
        screen: Bitmap,
        template: Bitmap,
        meta: JSONObject?,
        config: ActionConfig
    ): List<MatchCandidate> {

        val similarityThreshold = (config.similarityPercent / 100f).coerceIn(0.1f, 0.99f)
        val shapeOnly = config.shapeOnlyMode
        val hybridCascade = config.hybridCascadeMode
        val multiScale = config.multiScaleSearch

        val candidates = ArrayList<MatchCandidate>()

        val searchArea = if (config.customSearchArea) {
            Rect(
                (config.searchAreaXNorm * screen.width).toInt().coerceIn(0, screen.width - 1),
                (config.searchAreaYNorm * screen.height).toInt().coerceIn(0, screen.height - 1),
                ((config.searchAreaXNorm + config.searchAreaWNorm) * screen.width).toInt().coerceIn(1, screen.width),
                ((config.searchAreaYNorm + config.searchAreaHNorm) * screen.height).toInt().coerceIn(1, screen.height)
            )
        } else {
            Rect(0, 0, screen.width, screen.height)
        }

        val coarseStep = 6
        val fineStep = 2

        val scales = if (multiScale) {
            floatArrayOf(1.0f, 0.95f, 0.9f, 1.05f)
        } else {
            floatArrayOf(1.0f)
        }

        for (scale in scales) {
            val scaledTemplate = if (scale != 1.0f) {
                Bitmap.createScaledBitmap(
                    template,
                    (template.width * scale).toInt(),
                    (template.height * scale).toInt(),
                    true
                )
            } else template

            val tw = scaledTemplate.width
            val th = scaledTemplate.height

            for (y in searchArea.top until (searchArea.bottom - th).coerceAtLeast(searchArea.top + 1) step coarseStep) {
                for (x in searchArea.left until (searchArea.right - tw).coerceAtLeast(searchArea.left + 1) step coarseStep) {

                    val score = if (shapeOnly) {
                        shapeMatch(screen, scaledTemplate, x, y)
                    } else {
                        pixelMatch(screen, scaledTemplate, x, y)
                    }

                    if (score >= similarityThreshold) {
                        candidates.add(MatchCandidate(Rect(x, y, x + tw, y + th), score))
                    }
                }
            }

            val refined = ArrayList<MatchCandidate>()
            for (c in candidates) {
                val cx0 = max(searchArea.left, c.rect.left - coarseStep)
                val cy0 = max(searchArea.top, c.rect.top - coarseStep)
                val cx1 = min(searchArea.right - tw, c.rect.left + coarseStep)
                val cy1 = min(searchArea.bottom - th, c.rect.top + coarseStep)

                var bestScore = c.score
                var bestRect = c.rect

                for (y in cy0..cy1 step fineStep) {
                    for (x in cx0..cx1 step fineStep) {
                        val score = if (shapeOnly) {
                            shapeMatch(screen, scaledTemplate, x, y)
                        } else {
                            pixelMatch(screen, scaledTemplate, x, y)
                        }
                        if (score > bestScore) {
                            bestScore = score
                            bestRect = Rect(x, y, x + tw, y + th)
                        }
                    }
                }

                refined.add(MatchCandidate(bestRect, bestScore))
            }

            candidates.clear()
            candidates.addAll(refined)
        }

        if (hybridCascade) {
            return candidates.sortedByDescending { it.score }.take(3)
        }

        return candidates.sortedByDescending { it.score }
    }

    private fun pixelMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th) {
            for (x in 0 until tw) {
                if (sx + x >= screen.width || sy + y >= screen.height) continue
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val dr = abs(Color.red(sc) - Color.red(tc))
                val dg = abs(Color.green(sc) - Color.green(tc))
                val db = abs(Color.blue(sc) - Color.blue(tc))

                val diff = (dr + dg + db) / 765f
                val sim = 1f - diff

                score += sim
                total += 1f
            }
        }

        return if (total > 0f) score / total else 0f
    }

    private fun shapeMatch(screen: Bitmap, template: Bitmap, sx: Int, sy: Int): Float {
        val tw = template.width
        val th = template.height

        var score = 0f
        var total = 0f

        for (y in 0 until th step 2) {
            for (x in 0 until tw step 2) {
                if (sx + x >= screen.width || sy + y >= screen.height) continue
                val sc = screen.getPixel(sx + x, sy + y)
                val tc = template.getPixel(x, y)

                val scA = Color.alpha(sc)
                val tcA = Color.alpha(tc)

                val sim = if (tcA < 128) {
                    if (scA < 128) 1f else 0f
                } else {
                    if (scA >= 128) 1f else 0f
                }

                score += sim
                total += 1f
            }
        }

        return if (total > 0f) score / total else 0f
    }

    private fun applyCircularMask(bmp: Bitmap) {
        val w = bmp.width
        val h = bmp.height
        val cx = w / 2f
        val cy = h / 2f
        val r = min(w, h) / 2f

        for (y in 0 until h) {
            for (x in 0 until w) {
                val dx = x - cx
                val dy = y - cy
                if (dx * dx + dy * dy > r * r) {
                    bmp.setPixel(x, y, Color.TRANSPARENT)
                }
            }
        }
    }
}
"""
        with open(template_matcher_path, "w", encoding="utf-8") as f:
            f.write(template_matcher_code)
        print("  [✓] Обновлен TemplateMatcher.kt (добавлен aggregateMultiFrameMask)")

    # 3. Обновление TemplateRepository.kt (Явная типизация)
    template_repo_path = os.path.join("app", "src", "main", "java", "com", "example", "autotap", "data", "TemplateRepository.kt")
    if os.path.exists(template_repo_path):
        template_repo_code = r"""package com.example.autotap.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.widget.Toast
import com.example.autotap.MyAutoClickService
import com.example.autotap.TemplateMatcher
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream

class TemplateRepository(private val context: Context) {

    val globalTemplates = ArrayList<Bitmap>()
    val globalTemplatesNames = ArrayList<String>()

    fun getTemplateMetadataFile(maskPath: String): File {
        val maskFile = File(maskPath)
        val parent = maskFile.parentFile ?: context.filesDir
        val name = maskFile.nameWithoutExtension
        return File(parent, "${name}.json")
    }

    fun loadTemplateMetadata(maskPath: String): JSONObject? {
        try {
            if (maskPath.isEmpty()) return null
            val metaFile = getTemplateMetadataFile(maskPath)
            if (metaFile.exists()) {
                return JSONObject(metaFile.readText())
            }
        } catch (_: Exception) {}
        return null
    }

    fun loadFullBitmap(maskPath: String): Bitmap? {
        val maskFile = File(maskPath)
        val parent = maskFile.parentFile ?: return null
        val timestamp = maskFile.name.removePrefix("mask_").removeSuffix(".png")
        val fullFile = File(parent, "full_${timestamp}.png")
        if (!fullFile.exists()) return null
        return BitmapFactory.decodeFile(fullFile.absolutePath)
    }

    fun recordSuccessfulMatch(maskPath: String, matchPatch: Bitmap) {
        try {
            val maskFile = File(maskPath)
            if (!maskFile.exists()) return

            val name = maskFile.nameWithoutExtension
            val patchDir = File(File(context.filesDir, "templates/patches"), name).apply { mkdirs() }
            val patchFile = File(patchDir, "patch_${System.currentTimeMillis()}.png")

            FileOutputStream(patchFile).use { out ->
                matchPatch.compress(Bitmap.CompressFormat.PNG, 100, out)
            }

            val patchFiles = patchDir.listFiles()?.filter { file -> file.name.endsWith(".png") } ?: emptyList()
            if (patchFiles.size >= 5) {
                val patchBitmaps = patchFiles.mapNotNull { file -> BitmapFactory.decodeFile(file.absolutePath) }
                if (patchBitmaps.isNotEmpty()) {
                    val meta = loadTemplateMetadata(maskPath)
                    val isCircle = meta?.optBoolean("isCircleShape", true) ?: true

                    val consensusMask = TemplateMatcher.aggregateMultiFrameMask(
                        patchBitmaps,
                        isCircle
                    )

                    FileOutputStream(maskFile).use { out ->
                        consensusMask.compress(Bitmap.CompressFormat.PNG, 100, out)
                    }

                    if (meta != null) {
                        val currentVer = meta.optInt("version", 1)
                        meta.put("version", currentVer + 1)
                        val metaFile = getTemplateMetadataFile(maskPath)
                        FileOutputStream(metaFile).use { out ->
                            out.write(meta.toString().toByteArray(Charsets.UTF_8))
                        }
                    }

                    patchFiles.forEach { it.delete() }
                    patchDir.delete()

                    MyAutoClickService.logAppEvent(
                        context,
                        "SelfLearning",
                        "🧠 Маска '$name' пересобрана по 5 кадрам!"
                    )
                }
            }

        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun loadAllTemplatesFromDisk() {
        try {
            purgeOldTrashTemplates()

            globalTemplates.forEach {
                try { it.recycle() } catch (_: Exception) {}
            }
            globalTemplates.clear()
            globalTemplatesNames.clear()

            val baseDir = File(context.filesDir, "templates")
            if (baseDir.exists()) {
                val allMasks = baseDir.walkTopDown()
                    .filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }
                    .sortedBy { it.lastModified() }
                    .toList()

                allMasks.forEach { file ->
                    BitmapFactory.decodeFile(file.absolutePath)?.let { bmp ->
                        globalTemplates.add(bmp)
                        globalTemplatesNames.add(file.absolutePath)
                    }
                }
            }

            MyAutoClickService.logAppEvent(
                context,
                "Templates",
                "Загружено шаблонов: ${globalTemplates.size}"
            )

        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun moveTemplateToTrash(index: Int) {
        if (index !in globalTemplatesNames.indices) return

        try {
            val maskPath = globalTemplatesNames[index]
            val maskFile = File(maskPath)

            if (maskFile.exists()) {
                val dateFolder = maskFile.parentFile?.name ?: "default"
                val targetTrashDir = File(File(context.filesDir, "trash_templates"), dateFolder)
                    .apply { mkdirs() }

                maskFile.renameTo(File(targetTrashDir, maskFile.name))

                val timestamp = maskFile.name.removePrefix("mask_").removeSuffix(".png")
                val fullFile = File(maskFile.parentFile, "full_${timestamp}.png")
                if (fullFile.exists()) {
                    fullFile.renameTo(File(targetTrashDir, fullFile.name))
                }

                val metaFile = getTemplateMetadataFile(maskPath)
                if (metaFile.exists()) {
                    metaFile.renameTo(File(targetTrashDir, metaFile.name))
                }
            }

            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)

            Toast.makeText(context, "🗑 Шаблон перемещен в корзину", Toast.LENGTH_SHORT).show()

            MyAutoClickService.logAppEvent(
                context,
                "Templates",
                "Перемещен в корзину: $maskPath"
            )

        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    private fun purgeOldTrashTemplates() {
        try {
            val trashDir = File(context.filesDir, "trash_templates")
            if (!trashDir.exists()) return

            val now = System.currentTimeMillis()
            val sevenDaysMs = 7L * 24 * 60 * 60 * 1000L

            trashDir.walkTopDown().forEach { file ->
                if (file.isFile && (now - file.lastModified() > sevenDaysMs)) {
                    file.delete()
                }
            }

        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
"""
        with open(template_repo_path, "w", encoding="utf-8") as f:
            f.write(template_repo_code)
        print("  [✓] Обновлен TemplateRepository.kt")

    print("✨ Ошибки TemplateRepository и TemplateMatcher успешно устранены!")

if __name__ == "__main__":
    apply_template_matcher_repair()