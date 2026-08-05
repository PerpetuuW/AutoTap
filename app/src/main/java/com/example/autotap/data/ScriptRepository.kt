package com.example.autotap.data

import android.content.Context
import androidx.core.content.FileProvider
import com.example.autotap.ActionConfig
import com.example.autotap.MyAutoClickService
import org.json.JSONArray
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class ScriptRepository private constructor(private val context: Context) {

    companion object {
        @Volatile private var INSTANCE: ScriptRepository? = null

        fun init(context: Context): ScriptRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: ScriptRepository(context.applicationContext).also { INSTANCE = it }
            }
        }

        val instance: ScriptRepository
            get() = INSTANCE ?: throw IllegalStateException("ScriptRepository not initialized. Call init(context) first.")
    }

    private fun getScriptsDir(): File {
        val dir = File(context.filesDir, "scripts")
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun loadScriptByName(name: String): List<ActionConfig> {
        val list = ArrayList<ActionConfig>()
        try {
            val file = File(getScriptsDir(), "$name.json")
            val bakFile = File(getScriptsDir(), "$name.json.bak")
            val targetFile = if (file.exists() && file.length() > 0) file else bakFile

            if (targetFile != null && targetFile.exists()) {
                val jsonArray = JSONArray(targetFile.readText())
                for (i in 0 until jsonArray.length()) {
                    list.add(ActionConfig.fromJson(jsonArray.getJSONObject(i)))
                }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
        return list
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        try {
            val file = File(getScriptsDir(), "$name.json")
            val bakFile = File(getScriptsDir(), "$name.json.bak")
            if (file.exists()) file.copyTo(bakFile, overwrite = true)

            val jsonArray = JSONArray()
            actions.forEach { jsonArray.put(it.toJson()) }

            file.writeText(jsonArray.toString(2))
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }

    fun exportScriptWithTemplates(scriptName: String) {
        try {
            val scriptFile = File(getScriptsDir(), "$scriptName.json")
            if (!scriptFile.exists()) return

            val zipFile = File(context.externalCacheDir ?: context.cacheDir, "$scriptName.zip")
            val zos = ZipOutputStream(FileOutputStream(zipFile))
            zos.putNextEntry(ZipEntry("scripts/$scriptName.json"))
            zos.write(scriptFile.readBytes())
            zos.closeEntry()
            zos.close()

            val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", zipFile)
            val shareIntent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(android.content.Intent.EXTRA_STREAM, uri)
                addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(android.content.Intent.createChooser(shareIntent, "Экспорт сценария v35"))
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
