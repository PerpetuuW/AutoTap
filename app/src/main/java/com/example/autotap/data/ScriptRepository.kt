package com.example.autotap.data

import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.util.HashSet
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import com.example.autotap.*

class ScriptRepository(
    private val context: Context,
    private val templateRepository: TemplateRepository
) {
    private val lock = Any()

    fun saveScriptByName(name: String, actionsList: List<ActionConfig>): Boolean = synchronized(lock) {
        val scriptsDir = File(context.filesDir, "scripts").apply { mkdirs() }
        val targetFile = File(scriptsDir, "$name.json")
        val tempFile = File(scriptsDir, "$name.json.tmp")
        val backupFile = File(scriptsDir, "$name.json.bak")

        return try {
            val jsonArray = JSONArray()
            for (action in actionsList) {
                val obj = JSONObject().apply {
                    put("id", action.id)
                    put("type", action.type.name)
                    put("delay", action.delay)
                    put("repeatCount", action.repeatCount)
                    put("holdDuration", action.holdDuration)
                    put("randomRadius", action.randomRadius)

                    val templatePath = if (action.selectedTemplateIndex in templateRepository.globalTemplatesNames.indices) {
                        templateRepository.globalTemplatesNames[action.selectedTemplateIndex]
                    } else ""
                    val templateFileName = if (templatePath.isNotEmpty()) File(templatePath).name else ""

                    put("selectedTemplateIndex", action.selectedTemplateIndex)
                    put("templateFileName", templateFileName)
                    put("playAudioOnMatch", action.playAudioOnMatch)

                    val multiArr = JSONArray()
                    action.multiTemplateIndices.forEach { multiArr.put(it) }
                    put("multiTemplateIndices", multiArr)
                    put("clickAiTarget", action.clickAiTarget)
                    put("aiTimeoutSeconds", action.aiTimeoutSeconds)
                    put("similarityPercent", action.similarityPercent)
                    put("targetScriptToLoad", action.targetScriptToLoad)
                    put("jumpToStepOnMatch", action.jumpToStepOnMatch)
                    put("isFastMode", action.isFastMode)

                    val loc = IntArray(2)
                    action.startView.getLocationOnScreen(loc)
                    put("x", loc[0])
                    put("y", loc[1])
                    if (action.endView != null) {
                        val endLoc = IntArray(2)
                        action.endView!!.getLocationOnScreen(endLoc)
                        put("endX", endLoc[0])
                        put("endY", endLoc[1])
                    }
                }
                jsonArray.put(obj)
            }

            val dataString = jsonArray.toString(2)

            FileOutputStream(tempFile).use { fos ->
                fos.write(dataString.toByteArray(Charsets.UTF_8))
                fos.flush()
                fos.fd.sync()
            }

            if (tempFile.length() == 0L) {
                throw IllegalStateException("Temp file write failed, size is 0")
            }

            if (targetFile.exists()) {
                if (backupFile.exists()) backupFile.delete()
                targetFile.copyTo(backupFile, overwrite = true)
            }

            if (tempFile.renameTo(targetFile)) {
                Toast.makeText(context, "Сценарий '$name' сохранен!", Toast.LENGTH_SHORT).show()
                MyAutoClickService.logAppEvent(context, "Script", "Сценарий '$name' сохранен атомарно. Шагов: ${actionsList.size}")
                true
            } else {
                tempFile.copyTo(targetFile, overwrite = true)
                tempFile.delete()
                true
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
            if (backupFile.exists() && !targetFile.exists()) {
                backupFile.copyTo(targetFile, overwrite = true)
            }
            false
        }
    }

    fun exportScriptWithTemplates(exportContext: Context, scriptName: String) {
        try {
            val scriptsDir = File(exportContext.filesDir, "scripts")
            val scriptFile = File(scriptsDir, "$scriptName.json")
            if (!scriptFile.exists()) return

            val zipFile = File(exportContext.externalCacheDir ?: exportContext.cacheDir, "$scriptName.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))

            val jsonBytes = scriptFile.readBytes()
            val jsonEntry = ZipEntry("scripts/$scriptName.json")
            zos.putNextEntry(jsonEntry)
            zos.write(jsonBytes)
            zos.closeEntry()

            val jsonArray = runCatching { JSONArray(String(jsonBytes)) }.getOrNull() ?: JSONArray()
            val exportedTemplates = HashSet<String>()

            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.optJSONObject(i) ?: continue
                val tFileName = obj.optString("templateFileName", "")
                val idx = obj.optInt("selectedTemplateIndex", -1)

                val maskPath = if (tFileName.isNotEmpty()) {
                    templateRepository.globalTemplatesNames.firstOrNull { File(it).name == tFileName }
                        ?: if (idx in templateRepository.globalTemplatesNames.indices) templateRepository.globalTemplatesNames[idx] else null
                } else if (idx in templateRepository.globalTemplatesNames.indices) {
                    templateRepository.globalTemplatesNames[idx]
                } else null

                if (maskPath != null && !exportedTemplates.contains(maskPath)) {
                    exportedTemplates.add(maskPath)
                    val maskFile = File(maskPath)
                    if (maskFile.exists()) {
                        val dateFolder = maskFile.parentFile?.name ?: "default"

                        val maskEntry = ZipEntry("templates/$dateFolder/${maskFile.name}")
                        zos.putNextEntry(maskEntry)
                        zos.write(maskFile.readBytes())
                        zos.closeEntry()

                        val fullFile = File(maskFile.parentFile, maskFile.name.replace("mask_", "full_"))
                        if (fullFile.exists()) {
                            val fullEntry = ZipEntry("templates/$dateFolder/${fullFile.name}")
                            zos.putNextEntry(fullEntry)
                            zos.write(fullFile.readBytes())
                            zos.closeEntry()
                        }

                        val metaFile = templateRepository.getTemplateMetadataFile(maskPath)
                        if (metaFile.exists()) {
                            val metaEntry = ZipEntry("templates/$dateFolder/${metaFile.name}")
                            zos.putNextEntry(metaEntry)
                            zos.write(metaFile.readBytes())
                            zos.closeEntry()
                        }
                    }
                }
            }

            zos.close()

            val uri = try {
                FileProvider.getUriForFile(exportContext, "${exportContext.packageName}.fileprovider", zipFile)
            } catch (e: Exception) {
                MyAutoClickService.logError(exportContext, e)
                null
            }

            if (uri == null) {
                Toast.makeText(exportContext, "Ошибка доступа к ZIP-файлу!", Toast.LENGTH_SHORT).show()
                return
            }

            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(Intent.EXTRA_SUBJECT, scriptName)
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            exportContext.startActivity(Intent.createChooser(shareIntent, "Экспортировать").apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            })
            MyAutoClickService.logAppEvent(exportContext, "Export", "Сценарий '$scriptName' успешно экспортирован")
        } catch (e: Exception) {
            MyAutoClickService.logError(exportContext, e)
        }
    }
}
