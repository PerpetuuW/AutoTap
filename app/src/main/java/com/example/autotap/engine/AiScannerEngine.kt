package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Point
import android.os.Build
import android.util.Log
import kotlinx.coroutines.*
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import com.example.autotap.*

class AiScannerEngine {

    /**
     * Executes real multi-frame stabilization.
     * Captures N consecutive screen frames and calculates Spatial Consensus Mode.
     */
    suspend fun scanWithStabilization(
        action: AutoTapAction,
        frameCount: Int = 3
    ): Point? = withContext(Dispatchers.Default) {
        val service = AutoTapAccessibilityService.instance ?: return@withContext null
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return@withContext null

        val candidatePoints = mutableListOf<Point>()
        val parsedColor = try { Color.parseColor(action.targetColorHex) } catch (e: Exception) { Color.RED }

        repeat(frameCount) {
            val bitmap = service.captureScreenBitmap().await()
            if (bitmap != null) {
                val matches = HybridCascadeMatcher.match(bitmap, parsedColor, action.colorTolerance, action.searchRegion)
                if (matches.isNotEmpty()) {
                    candidatePoints.add(matches.first().point)
                }
                bitmap.recycle()
            }
            delay(50L)
        }

        if (candidatePoints.isEmpty()) return@withContext null

        // Calculate Spatial Consensus (cluster mode of points within 12px radius)
        val consensusPoint = candidatePoints.groupBy { pt ->
            "${pt.x / 12}_${pt.y / 12}"
        }.maxByOrNull { it.value.size }?.value?.firstOrNull()

        logStructured("Stabilized AI Scan consensus point: $consensusPoint from ${candidatePoints.size} frames")
        return@withContext consensusPoint
    }

    private fun logStructured(msg: String) {
        val time = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        Log.d("AiScannerEngine", "[$time] $msg")
    }
}
