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
        return File(parent, "${maskFile.nameWithoutExtension}.json")
    }

    fun loadTemplateMetadata(maskPath: String): JSONObject? {
        try {
            if (maskPath.isEmpty()) return null
            val metaFile = getTemplateMetadataFile(maskPath)
            if (metaFile.exists()) return JSONObject(metaFile.readText())
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

            FileOutputStream(patchFile).use { out -> matchPatch.compress(Bitmap.CompressFormat.PNG, 100, out) }

            val patchFiles = patchDir.listFiles()?.filter { file -> file.name.endsWith(".png") } ?: emptyList()
            if (patchFiles.size >= 5) {
                val patchBitmaps = patchFiles.mapNotNull<File, Bitmap> { file -> BitmapFactory.decodeFile(file.absolutePath) }
                if (patchBitmaps.isNotEmpty()) {
                    val meta = loadTemplateMetadata(maskPath)
                    val isCircle = meta?.optBoolean("isCircleShape", true) ?: true
                    val consensusMask = TemplateMatcher.aggregateMultiFrameMask(patchBitmaps, isCircle)

                    FileOutputStream(maskFile).use { out -> consensusMask.compress(Bitmap.CompressFormat.PNG, 100, out) }

                    if (meta != null) {
                        meta.put("version", meta.optInt("version", 1) + 1)
                        FileOutputStream(getTemplateMetadataFile(maskPath)).use { out ->
                            out.write(meta.toString().toByteArray(Charsets.UTF_8))
                        }
                    }

                    patchFiles.forEach { it.delete() }
                    patchDir.delete()
                }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun loadAllTemplatesFromDisk() {
        try {
            globalTemplates.forEach { try { it.recycle() } catch (_: Exception) {} }
            globalTemplates.clear()
            globalTemplatesNames.clear()

            val baseDir = File(context.filesDir, "templates")
            if (baseDir.exists()) {
                baseDir.walkTopDown()
                    .filter { it.isFile && it.name.startsWith("mask_") && it.name.endsWith(".png") }
                    .sortedBy { it.lastModified() }
                    .forEach { file ->
                        BitmapFactory.decodeFile(file.absolutePath)?.let { bmp ->
                            globalTemplates.add(bmp)
                            globalTemplatesNames.add(file.absolutePath)
                        }
                    }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun moveTemplateToTrash(index: Int) {
        if (index !in globalTemplatesNames.indices) return
        try {
            val maskPath = globalTemplatesNames[index]
            val maskFile = File(maskPath)
            if (maskFile.exists()) maskFile.delete()
            globalTemplates.removeAt(index)
            globalTemplatesNames.removeAt(index)
            Toast.makeText(context, "🗑 Шаблон удален", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
