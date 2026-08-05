package com.example.autotap
import com.example.autotap.*

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.autotap.core.AutoTapAccessibilityService
import com.example.autotap.data.ScenarioManager
import com.example.autotap.engine.ActionExecutor
import com.example.autotap.ui.OverlayManager

class MainActivity : AppCompatActivity() {

    private lateinit var scenarioManager: ScenarioManager
    private lateinit var actionExecutor: ActionExecutor
    private lateinit var overlayManager: OverlayManager

    private lateinit var tvStatusAccessibility: TextView
    private lateinit var tvStatusOverlay: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        scenarioManager = ScenarioManager(this)
        actionExecutor = ActionExecutor(scenarioManager)

        tvStatusAccessibility = findViewById(R.id.tvStatusAccessibility)
        tvStatusOverlay = findViewById(R.id.tvStatusOverlay)

        overlayManager = OverlayManager(
            context = this,
            scenarioManager = scenarioManager,
            onStartClick = { actionExecutor.startExecution() },
            onStopClick = { actionExecutor.stopExecution() }
        )

        findViewById<Button>(R.id.btnAccessibility).setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        findViewById<Button>(R.id.btnOverlayPermission).setOnClickListener {
            requestOverlayPermission()
        }

        findViewById<Button>(R.id.btnBatteryOptimization).setOnClickListener {
            ensureBatteryOptimizationIgnored()
        }

        findViewById<Button>(R.id.btnStartOverlay).setOnClickListener {
            if (checkOverlayPermission()) {
                overlayManager.showOverlay()
                Toast.makeText(this, "Плавающая панель запущена", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Требуется разрешение на оверлей!", Toast.LENGTH_SHORT).show()
                requestOverlayPermission()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        updateStatusIndicators()
    }

    private fun updateStatusIndicators() {
        val isServiceRunning = AutoTapAccessibilityService.instance != null
        tvStatusAccessibility.text = if (isServiceRunning) "Accessibility Service: АКТИВЕН" else "Accessibility Service: ОТКЛЮЧЕН"
        tvStatusAccessibility.setTextColor(if (isServiceRunning) getColor(R.color.accent_green) else getColor(R.color.accent_red))

        val hasOverlay = checkOverlayPermission()
        tvStatusOverlay.text = if (hasOverlay) "Overlay Permission: АКТИВЕН" else "Overlay Permission: ОТКЛЮЧЕН"
        tvStatusOverlay.setTextColor(if (hasOverlay) getColor(R.color.accent_green) else getColor(R.color.accent_red))
    }

    private fun ensureBatteryOptimizationIgnored() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            if (!pm.isIgnoringBatteryOptimizations(packageName)) {
                try {
                    val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                        data = Uri.parse("package:$packageName")
                    }
                    startActivity(intent)
                } catch (e: Exception) {
                    android.util.Log.e("MainActivity", "Battery optimization error: ${e.message}")
                }
            }
        }
    }

    private fun checkOverlayPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Settings.canDrawOverlays(this)
        } else true
    }

    private fun requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")
            )
            startActivity(intent)
        }
    }
}
