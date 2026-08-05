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

    fun validateJson(jsonStr: String): Boolean {
        return try {
            JSONArray(jsonStr)
            true
        } catch (_: Exception) {
            false
        }
    }

    fun loadScriptByName(name: String): List<ActionConfig> {
        val list = ArrayList<ActionConfig>()
        try {
            val file = File(getScriptsDir(), "$name.json")
            val bakFile = File(getScriptsDir(), "$name.json.bak")

            var targetContent: String? = null

            if (file.exists() && file.length() > 0) {
                val content = file.readText()
                if (validateJson(content)) {
                    targetContent = content
                }
            }

            if (targetContent == null && bakFile.exists() && bakFile.length() > 0) {
                val bakContent = bakFile.readText()
                if (validateJson(bakContent)) {
                    targetContent = bakContent
                    MyAutoClickService.logAppEvent(context, "ScriptRepo", "Восстановлен сценарий '$name' из бэкапа .bak!")
                }
            }

            if (targetContent != null) {
                val jsonArray = JSONArray(targetContent)
                for (i in 0 until jsonArray.length()) {
                    val cfg = ActionConfig.fromJson(jsonArray.getJSONObject(i))
                    if (cfg.version < 35) {
                        cfg.version = 35
                        cfg.updatedAt = System.currentTimeMillis()
                    }
                    list.add(cfg)
                }
            }
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
        return list
    }

    fun saveScriptByName(name: String, actions: List<ActionConfig>) {
        try {
            val dir = getScriptsDir()
            val file = File(dir, "$name.json")
            val tmpFile = File(dir, "$name.tmp")
            val bakFile = File(dir, "$name.json.bak")

            if (file.exists() && file.length() > 0) {
                file.copyTo(bakFile, overwrite = true)
            }

            val jsonArray = JSONArray()
            actions.forEach { cfg ->
                cfg.updatedAt = System.currentTimeMillis()
                jsonArray.put(cfg.toJson())
            }

            val jsonStr = jsonArray.toString(2)

            tmpFile.writeText(jsonStr)
            if (validateJson(tmpFile.readText())) {
                tmpFile.copyTo(file, overwrite = true)
                tmpFile.delete()
            }

            MyAutoClickService.logAppEvent(context, "ScriptRepo", "Atomic-Save: Сценарий '$name' сохранен (${actions.size} шагов).")
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
