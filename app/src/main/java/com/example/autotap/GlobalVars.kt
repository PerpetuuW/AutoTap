package com.example.autotap

import java.util.concurrent.CopyOnWriteArrayList

var isRecording: Boolean = false
var isPlaying: Boolean = false
var globalClickDurationMs: Long = 100L
var globalScriptLoopCount: Int = 1
var isGlobalScriptInfinite: Boolean = false
var globalRelayNextScript: String = ""

val globalTemplatesNames: MutableList<String> = CopyOnWriteArrayList()
val globalTemplates: MutableList<Any> = CopyOnWriteArrayList()
