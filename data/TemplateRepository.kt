package com.example.autotap.data

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
            if (!metaFile.exists()) return null

            val raw = metaFile.readText()
            val meta = try {
                JSONObject(raw)
            } catch (e: Exception) {
                MyAutoClickService.logError(context, e)
                return null
            }

            // авто‑миграция версии метаданных к v3+
            val curVer = meta.optInt("version", 1)
            if (curVer < 3) {
                meta.put("version", 3)
                FileOutputStream(metaFile).use { out ->
                    out.write(meta.toString().toByteArray())
                }
            }
            return meta
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
        return null
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

            val patchFiles = patchDir.listFiles()?.filter { it.name.endsWith(".png") } ?: emptyList()
            if (patchFiles.size >= 5) {
                val patchBitmaps = patchFiles.mapNotNull { f ->
                    try {
                        BitmapFactory.decodeFile(f.absolutePath)
                    } catch (_: Exception) {
                        null
                    }
                }
                if (patchBitmaps.isNotEmpty()) {
                    val meta = loadTemplateMetadata(maskPath)
                    val isCircle = meta?.optBoolean("isCircleShape", true) ?: true
                    val consensusMask = TemplateMatcher.aggregateMultiFrameMask(patchBitmaps, isCircle)

                    FileOutputStream(maskFile).use { out ->
                        consensusMask.compress(Bitmap.CompressFormat.PNG, 100, out)
                    }

                    if (meta != null) {
                        val currentVer = meta.optInt("version", 3)
                        meta.put("version", currentVer + 1)
                        val metaFile = getTemplateMetadataFile(maskPath)
                        FileOutputStream(metaFile).use { out -> out.write(meta.toString().toByteArray()) }
                    }

                    patchFiles.forEach { it.delete() }
                    patchDir.delete()
                    MyAutoClickService.logAppEvent(context, "SelfLearning", "🧠 Маска '$name' пересобрана и самообучена по 5 кликам!")
                } else {
                    // если патчи битые — просто очищаем директорию
                    patchFiles.forEach { it.delete() }
                    patchDir.delete()
                    MyAutoClickService.logAppEvent(context, "SelfLearning", "⚠ Патчи для маски '$name' были повреждены и очищены")
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
            TemplateCache.clear()

            val baseDir = File(context.filesDir, "templates")
            if (baseDir.exists()) {
                val allMasks = baseDir.walkTopDown()
                    .filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }
                    .sortedBy { it.lastModified() }
                    .toList()

                allMasks.forEach { file ->
                    try {
                        val opts = BitmapFactory.Options().apply {
                            inPreferredConfig = Bitmap.Config.ARGB_8888
                            inDither = false
                            inScaled = false
                        }
                        val bmp = BitmapFactory.decodeFile(file.absolutePath, opts)
                        if (bmp != null) {
                            globalTemplates.add(bmp)
                            globalTemplatesNames.add(file.absolutePath)
                            TemplateCache.put(file.absolutePath, bmp)
                        } else {
                            // битая маска — отправляем в корзину
                            MyAutoClickService.logAppEvent(context, "Templates", "⚠ Битая маска удалена: ${file.absolutePath}")
                            file.delete()
                        }
                    } catch (e: Exception) {
                        MyAutoClickService.logError(context, e)
                        file.delete()
                    }
                }
            }
            MyAutoClickService.logAppEvent(context, "Templates", "Загружено ИИ-шаблонов с диска: ${globalTemplates.size}")
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
                val targetTrashDir = File(File(context.filesDir, "trash_templates"), dateFolder).apply { mkdirs() }
                maskFile.renameTo(File(targetTrashDir, maskFile.name))
            }
            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)
            Toast.makeText(context, "🗑 Шаблон перемещен в корзину", Toast.LENGTH_SHORT).show()
            MyAutoClickService.logAppEvent(context, "Templates", "Перемещен в корзину шаблон #$index: $maskPath")
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    private fun purgeOldTrashTemplates() {
        try {
            val trashDir = File(context.filesDir, "trash_templates")
            if (trashDir.exists()) {
                val now = System.currentTimeMillis()
                val sevenDaysMs = 7L * 24 * 60 * 60 * 1000L
                trashDir.walkTopDown().forEach { file ->
                    if (file.isFile && (now - file.lastModified() > sevenDaysMs)) {
                        file.delete()
                    }
                }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
