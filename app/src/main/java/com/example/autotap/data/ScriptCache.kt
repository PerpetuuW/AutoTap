
package com.example.autotap.data
import com.example.autotap.*

import org.json.JSONArray
import java.util.concurrent.ConcurrentHashMap

object ScriptCache {
    private val cache = ConcurrentHashMap<String, JSONArray>()

    fun get(name: String): JSONArray? = cache[name]

    fun put(name: String, arr: JSONArray) {
        cache[name] = arr
    }

    fun clear() = cache.clear()
}
