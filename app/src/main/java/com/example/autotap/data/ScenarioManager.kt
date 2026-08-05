package com.example.autotap.data

import android.content.Context
import android.util.Log
import org.json.JSONArray
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CopyOnWriteArrayList
import com.example.autotap.*

class ScenarioManager(private val context: Context) {

    private val actionsList = CopyOnWriteArrayList<AutoTapAction>()
    private val lock = Any()

    fun getActions(): List<AutoTapAction> = actionsList.toList()

    fun addAction(action: AutoTapAction) {
        action.index = actionsList.size + 1
        actionsList.add(action)
        logEvent("Action #${action.index} added at (${action.x}, ${action.y})")
    }

    fun removeLastAction(): AutoTapAction? {
        if (actionsList.isNotEmpty()) {
            val removed = actionsList.removeAt(actionsList.size - 1)
            logEvent("Action #${removed.index} removed")
            return removed
        }
        return null
    }

    fun clearActions() {
        actionsList.clear()
        logEvent("All actions cleared")
    }

    fun saveScenarioAtomic(fileName: String = "default_scenario.json"): Boolean = synchronized(lock) {
        val targetFile = File(context.filesDir, fileName)
        val tempFile = File(context.filesDir, "$fileName.tmp")
        val backupFile = File(context.filesDir, "$fileName.bak")

        return try {
            val jsonArray = JSONArray()
            actionsList.forEach { jsonArray.put(it.toJson()) }
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
                logEvent("Scenario saved atomically to ${targetFile.absolutePath}")
                true
            } else {
                tempFile.copyTo(targetFile, overwrite = true)
                tempFile.delete()
                logEvent("Scenario saved via fallback copy to ${targetFile.absolutePath}")
                true
            }
        } catch (e: Exception) {
            logEvent("ERROR saving scenario: ${e.message}")
            Log.e("ScenarioManager", "Atomic save failed", e)
            if (backupFile.exists() && !targetFile.exists()) {
                backupFile.copyTo(targetFile, overwrite = true)
            }
            false
        }
    }

    fun loadScenario(fileName: String = "default_scenario.json"): Boolean = synchronized(lock) {
        val targetFile = File(context.filesDir, fileName)
        val fileToRead = if (targetFile.exists()) targetFile else File(context.filesDir, "$fileName.bak")

        if (!fileToRead.exists()) {
            logEvent("No scenario file found to load")
            return false
        }

        return try {
            val content = fileToRead.readText(Charsets.UTF_8)
            val jsonArray = JSONArray(content)
            actionsList.clear()
            for (i in 0 until jsonArray.length()) {
                val action = AutoTapAction.fromJson(jsonArray.getJSONObject(i))
                actionsList.add(action)
            }
            logEvent("Loaded ${actionsList.size} actions from ${fileToRead.name}")
            true
        } catch (e: Exception) {
            logEvent("ERROR loading scenario: ${e.message}")
            Log.e("ScenarioManager", "Failed to load scenario", e)
            false
        }
    }

    private fun logEvent(message: String) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        Log.d("ScenarioManager", "[$timestamp] $message")
    }
}
