import os
import sys
import re

def validate_kotlin(content, filename):
    # 1. Удаляем комментарии и строковые литералы перед проверкой скобок
    clean = re.sub(r'/\*[\s\S]*?\*/', '', content)
    clean = re.sub(r'//.*', '', clean)
    clean = re.sub(r'"""[\s\S]*?"""', '""', clean)
    clean = re.sub(r'"([^"\\]|\\.)*"', '""', clean)
    clean = re.sub(r"'([^'\\]|\\.)*'", "''", clean)

    brackets = {'(': ')', '{': '}', '[': ']'}
    stack = []
    for char in clean:
        if char in brackets.keys():
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Лишняя закрывающая скобка '{char}'")
            top = stack.pop()
            if brackets[top] != char:
                raise ValueError(f"Ошибка синтаксиса в {filename}: Несоответствие скобок '{top}' и '{char}'")
    if stack:
        raise ValueError(f"Ошибка синтаксиса в {filename}: Незакрытые скобки {stack}")

    forbidden = ["TODO()", "// остальной код", "// TODO"]
    for item in forbidden:
        if item in content:
            raise ValueError(f"Обнаружена запрещенная заглушка '{item}' в файле {filename}")

files = {}

# 1. TemplateMatcher.kt — Чистые импорты
files["app/src/main/java/com/example/autotap/engine/ai/TemplateMatcher.kt"] = """package com.example.autotap.engine.ai

import android.graphics.Bitmap
import android.graphics.Rect
import com.example.autotap.data.TemplateRepository
import com.example.autotap.model.ActionConfig

class TemplateMatcher(private val repository: TemplateRepository) {

    private val cascadeMatcher = HybridCascadeMatcher()

    fun matchSingleTemplate(frame: Bitmap, action: ActionConfig): List<MatchCandidate> {
        val calibrated = repository.loadCalibratedMask(action.selectedTemplateIndex)
        val mask = calibrated?.original ?: repository.loadTemplate(action.selectedTemplateIndex) ?: return emptyList()
        val profile = calibrated?.metadata?.profile ?: TemplateProfile.MEDIUM

        val searchArea = buildProfileAwareSearchArea(action, frame, profile)
        val searchModes = buildProfileAwareModes(action, profile)

        return cascadeMatcher.match(frame, mask, searchArea, searchModes, action.similarityPercent / 100f)
    }

    fun matchMultiTemplate(frame: Bitmap, action: ActionConfig): List<MatchCandidate> {
        val indices = if (action.multiTemplateIndices.isNotEmpty()) {
            action.multiTemplateIndices
        } else {
            listOf(action.selectedTemplateIndex)
        }

        val allCandidates = mutableListOf<MatchCandidate>()

        for (index in indices) {
            val calibrated = repository.loadCalibratedMask(index)
            val mask = calibrated?.original ?: repository.loadTemplate(index) ?: continue
            val profile = calibrated?.metadata?.profile ?: TemplateProfile.MEDIUM

            val searchArea = buildProfileAwareSearchArea(action, frame, profile)
            val searchModes = buildProfileAwareModes(action, profile)

            val candidates = cascadeMatcher.match(frame, mask, searchArea, searchModes, action.similarityPercent / 100f)
            for (c in candidates) {
                allCandidates.add(c.copy(templateIndex = index))
            }
        }

        return rankCandidates(allCandidates)
    }

    fun rankCandidates(candidates: List<MatchCandidate>): List<MatchCandidate> {
        return candidates.sortedByDescending { it.score }
    }

    private fun buildProfileAwareModes(action: ActionConfig, profile: TemplateProfile): SearchModes {
        return when (profile) {
            TemplateProfile.SMALL -> SearchModes(
                shapeOnlyMode = action.shapeOnlyMode,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = action.multiScaleSearch,
                contourWeight = 0.4f,
                pixelWeight = 0.6f,
                scaleBoost = 0.25f,
                profile = profile
            )
            TemplateProfile.LARGE -> SearchModes(
                shapeOnlyMode = action.shapeOnlyMode,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = action.multiScaleSearch,
                contourWeight = 0.2f,
                pixelWeight = 0.8f,
                scaleBoost = -0.25f,
                profile = profile
            )
            TemplateProfile.THIN_LINE -> SearchModes(
                shapeOnlyMode = true,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = false,
                contourWeight = 0.85f,
                pixelWeight = 0.15f,
                scaleBoost = 0.0f,
                profile = profile
            )
            else -> SearchModes(
                shapeOnlyMode = action.shapeOnlyMode,
                autoTuningMode = action.autoTuningMode,
                hybridCascadeMode = action.hybridCascadeMode,
                multiScaleSearch = action.multiScaleSearch,
                contourWeight = 0.3f,
                pixelWeight = 0.7f,
                scaleBoost = 0.0f,
                profile = profile
            )
        }
    }

    private fun buildProfileAwareSearchArea(action: ActionConfig, frame: Bitmap, profile: TemplateProfile): Rect {
        if (action.customSearchArea) {
            return Rect(
                action.searchAreaX.coerceIn(0, frame.width),
                action.searchAreaY.coerceIn(0, frame.height),
                (action.searchAreaX + action.searchAreaW).coerceIn(0, frame.width),
                (action.searchAreaY + action.searchAreaH).coerceIn(0, frame.height)
            )
        }

        return Rect(0, 0, frame.width, frame.height)
    }
}
"""

# 2. ScriptRepository.kt — Публичное свойство currentMetadata c корректным считыванием JSON
files["app/src/main/java/com/example/autotap/data/ScriptRepository.kt"] = """package com.example.autotap.data

import android.content.Context
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.model.ActionConfig
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class ScriptRepository(private val context: Context) {

    private val cache = mutableMapOf<String, List<ActionConfig>>()
    var currentMetadata: ScriptMetadata? = null

    fun saveScript(name: String, actions: List<ActionConfig>, metadata: ScriptMetadata = ScriptMetadata(name = name, stepCount = actions.size)): Boolean {
        return try {
            val file = File(context.filesDir, "$name.json")
            val rootObj = JSONObject()

            rootObj.put("metadata", metadata.toJson())

            val actionsArray = JSONArray()
            for (action in actions) {
                val actionObj = JSONObject().apply {
                    put("type", action.type.name)
                    put("xNorm", action.xNorm)
                    put("yNorm", action.yNorm)
                    put("endXNorm", action.endXNorm)
                    put("endYNorm", action.endYNorm)
                    put("delay", action.delay)
                    put("holdDuration", action.holdDuration)
                    put("similarityPercent", action.similarityPercent)
                    put("selectedTemplateIndex", action.selectedTemplateIndex)
                    put("customSearchArea", action.customSearchArea)
                    put("searchAreaX", action.searchAreaX)
                    put("searchAreaY", action.searchAreaY)
                    put("searchAreaW", action.searchAreaW)
                    put("searchAreaH", action.searchAreaH)
                }
                actionsArray.put(actionObj)
            }
            rootObj.put("actions", actionsArray)

            file.writeText(rootObj.toString(2))
            cache[name] = actions.toList()
            currentMetadata = metadata
            logDiagnostic("SCRIPT", "Сценарий '$name' успешно сохранен в JSON (${actions.size} шагов).")
            true
        } catch (e: Exception) {
            logError("SCRIPT", "Ошибка сохранения сценария '$name'", e)
            false
        }
    }

    fun loadScript(name: String): List<ActionConfig> {
        if (cache.containsKey(name)) {
            val cached = cache[name] ?: emptyList()
            logDiagnostic("SCRIPT", "Сценарий '$name' загружен из кэша.")
            return cached
        }

        return try {
            val file = File(context.filesDir, "$name.json")
            if (!file.exists()) {
                logDiagnostic("SCRIPT", "Файл сценария '$name' не найден.")
                return emptyList()
            }
            val content = file.readText()
            val list = mutableListOf<ActionConfig>()

            if (content.trim().startsWith("{")) {
                val rootObj = JSONObject(content)
                if (rootObj.has("metadata")) {
                    currentMetadata = ScriptMetadata.fromJson(rootObj.getJSONObject("metadata"))
                }
                val actionsArray = rootObj.optJSONArray("actions") ?: JSONArray()
                for (i in 0 until actionsArray.length()) {
                    val obj = actionsArray.getJSONObject(i)
                    val config = ActionConfig(
                        xNorm = obj.optDouble("xNorm", 0.5).toFloat(),
                        yNorm = obj.optDouble("yNorm", 0.5).toFloat(),
                        endXNorm = obj.optDouble("endXNorm", 0.5).toFloat(),
                        endYNorm = obj.optDouble("endYNorm", 0.5).toFloat(),
                        delay = obj.optLong("delay", 500L),
                        holdDuration = obj.optLong("holdDuration", 100L),
                        similarityPercent = obj.optInt("similarityPercent", 85),
                        selectedTemplateIndex = obj.optInt("selectedTemplateIndex", 0),
                        customSearchArea = obj.optBoolean("customSearchArea", false),
                        searchAreaX = obj.optInt("searchAreaX", 0),
                        searchAreaY = obj.optInt("searchAreaY", 0),
                        searchAreaW = obj.optInt("searchAreaW", 0),
                        searchAreaH = obj.optInt("searchAreaH", 0)
                    )
                    list.add(config)
                }
            }
            cache[name] = list
            logDiagnostic("SCRIPT", "Сценарий '$name' загружен из JSON (${list.size} шагов).")
            list
        } catch (e: Exception) {
            logError("SCRIPT", "Ошибка загрузки сценария '$name'", e)
            emptyList()
        }
    }
}
"""

# 3. InfoHelpDialog.kt — Без многострочных эскейпов
files["app/src/main/java/com/example/autotap/ui/overlays/InfoHelpDialog.kt"] = """package com.example.autotap.ui.overlays

import android.content.Context
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.findViewByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority

class InfoHelpDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    private var tvContent: TextView? = null

    init {
        width = WindowManager.LayoutParams.MATCH_PARENT
        height = WindowManager.LayoutParams.WRAP_CONTENT
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.7f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_info, null)

        tvContent = view.findViewByNames("tvTabContent") as? TextView

        val versionName = try {
            context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: context.getString(R.string.app_version)
        } catch (_: Exception) {
            context.getString(R.string.app_version)
        }

        tvContent?.text = "AutoTap PRO (" + versionName + ")\n\nСправка по автоматизации и ИИ-поиску масок."

        view.bindClickByNames("tabClick") {
            tvContent?.text = "Справка по Кликам:\n• Длительность настраивается от 10мс до 1000мс.\n• Доступна случайная координатная погрешность (джиттер)."
            logDiagnostic("UI", "Переключение таба CLICK в InfoHelpDialog.")
        }

        view.bindClickByNames("tabSwipe") {
            tvContent?.text = "Справка по Свайпам:\n• Плавные свайпы и траектории джойстика с частотой 25 FPS.\n• Отображение стартового и конечного маркеров."
            logDiagnostic("UI", "Переключение таба SWIPE в InfoHelpDialog.")
        }

        view.bindClickByNames("tabAi") {
            tvContent?.text = "Справка по ИИ-Поиску (" + versionName + "):\n• Семейства масок: Small, Medium, Large, Thin-Line.\n• Реактивный мультипоиск со свежими кадрами экрана."
            logDiagnostic("UI", "Переключение таба AI в InfoHelpDialog.")
        }

        view.bindClickByNames("btnCloseInfoDialog") {
            logDiagnostic("UI", "Закрыта справка btnCloseInfoDialog.")
            hide()
        }

        return view
    }
}
"""

print("=== ПРИМЕНЕНИЕ УМНОГО ВАЛИДАТОРА СКОБОК ===")

for rel_path, content in files.items():
    abs_path = os.path.abspath(rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if rel_path.endswith(".kt"):
        validate_kotlin(content, rel_path)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"SUCCESS: {rel_path}")

print("=== ПАТЧИНГ УСПЕШНО ЗАВЕРШЕН ===")