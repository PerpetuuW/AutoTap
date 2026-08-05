
package com.example.autotap.data
import com.example.autotap.*

import android.graphics.Bitmap
import java.util.concurrent.ConcurrentHashMap

object TemplateCache {
    private val bitmaps = ConcurrentHashMap<String, Bitmap>()

    fun get(path: String): Bitmap? = bitmaps[path]

    fun put(path: String, bmp: Bitmap) {
        bitmaps[path] = bmp
    }

    fun remove(path: String) {
        bitmaps.remove(path)?.let {
            try { it.recycle() } catch (_: Exception) {}
        }
    }

    fun clear() {
        bitmaps.values.forEach {
            try { it.recycle() } catch (_: Exception) {}
        }
        bitmaps.clear()
    }
}
