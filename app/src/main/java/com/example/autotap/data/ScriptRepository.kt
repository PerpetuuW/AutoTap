package com.example.autotap.data

import android.content.Context
import com.example.autotap.ActionConfig
import com.example.autotap.MyAutoClickService
import org.json.JSONArray
import java.io.File

class ScriptRepository(private val context: Context) {

    private fun getScriptsDir(): File {
        val dir = File(context.filesDir, "scripts")
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun loadScriptByName(name: String): List<ActionConfig> {
        val list = ArrayList<ActionConfig>()
        try {
            val file = File(getScriptsDir(), "$name.json")
            if (file.exists()) {
                val jsonStr = file.readText()
                val jsonArray = JSONArray(jsonStr)
                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    list.add(ActionConfig.fromJson(obj))
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
            val jsonArray = JSONArray()
            actions.forEach { cfg ->
                jsonArray.put(cfg.toJson())
            }
            file.writeText(jsonArray.toString(2))
        } catch (e: Exception) {
            MyAutoClickService.logError(context, e)
        }
    }
}
