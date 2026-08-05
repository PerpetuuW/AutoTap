package com.example.autotap

import com.example.autotap.*

import android.graphics.Bitmap
import android.graphics.Rect
import android.graphics.RectF
import android.view.View
import java.io.File

open class OverlaySupport {
    var rootView: View? = null
    open fun show() {}
    open fun hide() {}
    open fun update(vararg args: Any?) {}
}

class DebuggerOverlaySupport : OverlaySupport()
class CaptureFrameOverlaySupport : OverlaySupport()
class JoystickOverlaySupport : OverlaySupport()

class AiScannerEngineSupport {
    fun scanForMatch(vararg args: Any?, callback: ((Boolean) -> Unit)? = null) { callback?.invoke(true) }
    fun executeAiTriggerSequence(vararg args: Any?) {}
    fun startTemplateCalibration(vararg args: Any?) {}
}

class TemplateRepositorySupport {
    fun getTemplateMetadataFile(name: String): File = File(name)
    fun write(name: String, data: ByteArray) {}
    fun loadAllTemplatesFromDisk() {}
    fun moveTemplateToTrash(target: Any) {}
}
