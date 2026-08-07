package com.example.autotap

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.example.autotap.data.ScriptRepository
import com.example.autotap.data.TemplateRepository
import com.example.autotap.engine.RecordingEngine
import com.example.autotap.engine.ai.MaskCalibrator
import com.example.autotap.model.ActionConfig
import com.example.autotap.model.ActionType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AutoTapFullSystemTest {

    private lateinit var context: Context
    private lateinit var templateRepository: TemplateRepository
    private lateinit var scriptRepository: ScriptRepository
    private lateinit var calibrator: MaskCalibrator

    @Before
    fun setUp() {
        context = InstrumentationRegistry.getInstrumentation().targetContext
        templateRepository = TemplateRepository(context)
        scriptRepository = ScriptRepository(context)
        calibrator = MaskCalibrator()
    }

    @Test
    fun test01TemplateSaveAndCalibrationPipeline() {
        val sampleBitmap = Bitmap.createBitmap(100, 100, Bitmap.Config.ARGB_8888).apply {
            eraseColor(Color.RED)
        }
        val nextIndex = templateRepository.getNextFreeTemplateIndex()
        val saved = templateRepository.saveTemplate(nextIndex, sampleBitmap)
        assertTrue("Ошибка сохранения шаблона маски", saved)

        val calibrated = templateRepository.loadCalibratedMask(nextIndex)
        assertNotNull("Калиброванная маска не должна быть null", calibrated)
        assertEquals(100, calibrated!!.boundingBox.width())
        assertEquals(100, calibrated.boundingBox.height())
        assertTrue("Рекомендованный порог симилярности должен быть >= 75%", calibrated.metadata.recommendedSimilarity >= 75)
    }

    @Test
    fun test02ScriptRepositorySaveAndLoadJson() {
        val actions = listOf(
            ActionConfig(type = ActionType.CLICK, xNorm = 0.3f, yNorm = 0.4f, delay = 200L),
            ActionConfig(type = ActionType.AI_SEARCH, selectedTemplateIndex = 0, similarityPercent = 85)
        )
        val scriptName = "test_auto_script"
        val saved = scriptRepository.saveScript(scriptName, actions)
        assertTrue("Ошибка сохранения сценария JSON", saved)

        val loaded = scriptRepository.loadScript(scriptName)
        assertEquals(2, loaded.size)
        assertEquals(ActionType.CLICK, loaded[0].type)
        assertEquals(ActionType.AI_SEARCH, loaded[1].type)
    }

    @Test
    fun test03RecordingEngineThreadSafety() {
        val service = MyAutoClickService().apply {
            scriptRepository = ScriptRepository(context)
            templateRepository = TemplateRepository(context)
        }
        val recordingEngine = RecordingEngine(service)
        recordingEngine.startRecording()
        recordingEngine.recordClick(0.5f, 0.5f)
        recordingEngine.recordSwipe(0.1f, 0.1f, 0.8f, 0.8f, 300L)

        assertEquals(2, recordingEngine.recordedActions.size)
        recordingEngine.stopRecording("test_rec_script")
        assertFalse(recordingEngine.isRecording)
    }
}
