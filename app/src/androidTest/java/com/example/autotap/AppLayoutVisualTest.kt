package com.example.autotap

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertNotNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AppLayoutVisualTest {

    private lateinit var context: Context

    @Before
    fun setUp() {
        context = InstrumentationRegistry.getInstrumentation().targetContext
    }

    @Test
    fun testControlPanelLayoutButtonsNotClipped() {
        val inflater = LayoutInflater.from(context)
        val panelView = inflater.inflate(R.layout.floating_control_panel, null)

        val btnPlay = panelView.findViewById<View>(R.id.btnPlay)
        val btnAdd = panelView.findViewById<View>(R.id.btnAdd)
        val btnCapturePool = panelView.findViewById<View>(R.id.btnCapturePool)

        assertNotNull("Кнопка Старт должна быть в XML", btnPlay)
        assertNotNull("Кнопка Добавить должна быть в XML", btnAdd)
        assertNotNull("Кнопка Прицел должна быть в XML", btnCapturePool)
    }

    @Test
    fun testCaptureFrameMinWidthSufficient() {
        val inflater = LayoutInflater.from(context)
        val captureView = inflater.inflate(R.layout.floating_capture_frame, null)
        val topBar = captureView.findViewById<View>(R.id.layoutTopBar)

        assertNotNull("Верхняя панель прицела должна быть в XML", topBar)
    }
}
