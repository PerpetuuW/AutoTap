package com.example.autotap

import com.example.autotap.*

import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var statusAccessibilityTv: TextView
    private lateinit var statusOverlayTv: TextView
    private lateinit var statusBatteryTv: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        logAppEvent("MainActivity_onCreate")

        val scrollView = ScrollView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(Color.parseColor("#121212"))
        }

        val rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 60, 40, 60)
            gravity = Gravity.CENTER_HORIZONTAL
        }

        val titleTv = TextView(this).apply {
            text = "AutoTap Dashboard"
            setTextColor(Color.WHITE)
            textSize = 26f
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, 40)
        }
        rootLayout.addView(titleTv)

        statusAccessibilityTv = createStatusCard(rootLayout, "Accessibility Service: UNKNOWN")
        val btnAccessibility = createButton("Enable Accessibility Service") {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            startActivity(intent)
        }
        rootLayout.addView(btnAccessibility)

        statusOverlayTv = createStatusCard(rootLayout, "Overlay Permission: UNKNOWN")
        val btnOverlay = createButton("Grant Overlay Permission") {
            if (!Settings.canDrawOverlays(this)) {
                val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
                startActivity(intent)
            }
        }
        rootLayout.addView(btnOverlay)

        statusBatteryTv = createStatusCard(rootLayout, "Battery Optimization: UNKNOWN")
        val btnBattery = createButton("Ignore Battery Optimizations") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
                if (!pm.isIgnoringBatteryOptimizations(packageName)) {
                    val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
                    startActivity(intent)
                }
            }
        }
        rootLayout.addView(btnBattery)

        val btnLaunchOverlay = Button(this).apply {
            text = "LAUNCH FLOATING PANEL"
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#FF5722"))
            textSize = 16f
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 30, 0, 30)
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 50, 0, 0) }
            layoutParams = lp

            setOnClickListener {
                vibrateFeedback(50L)
                if (MyAutoClickService.instance != null) {
                    MyAutoClickService.instance?.showControlPanel()
                    moveTaskToBack(true)
                } else {
                    val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    startActivity(intent)
                }
            }
        }
        rootLayout.addView(btnLaunchOverlay)

        scrollView.addView(rootLayout)
        setContentView(scrollView)
    }

    override fun onResume() {
        super.onResume()
        updateDashboardStatuses()
    }

    private fun updateDashboardStatuses() {
        val isServiceConnected = MyAutoClickService.instance != null
        if (isServiceConnected) {
            statusAccessibilityTv.text = "● Accessibility Service: ACTIVE"
            statusAccessibilityTv.setTextColor(Color.parseColor("#4CAF50"))
        } else {
            statusAccessibilityTv.text = "● Accessibility Service: DISABLED"
            statusAccessibilityTv.setTextColor(Color.parseColor("#F44336"))
        }

        val canOverlay = Settings.canDrawOverlays(this)
        if (canOverlay) {
            statusOverlayTv.text = "● Overlay Permission: GRANTED"
            statusOverlayTv.setTextColor(Color.parseColor("#4CAF50"))
        } else {
            statusOverlayTv.text = "● Overlay Permission: MISSING"
            statusOverlayTv.setTextColor(Color.parseColor("#F44336"))
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            val isIgnoring = pm.isIgnoringBatteryOptimizations(packageName)
            if (isIgnoring) {
                statusBatteryTv.text = "● Battery Optimization: EXEMPTED"
                statusBatteryTv.setTextColor(Color.parseColor("#4CAF50"))
            } else {
                statusBatteryTv.text = "● Battery Optimization: RESTRICTED"
                statusBatteryTv.setTextColor(Color.parseColor("#FF9800"))
            }
        } else {
            statusBatteryTv.text = "● Battery Optimization: OK"
            statusBatteryTv.setTextColor(Color.parseColor("#4CAF50"))
        }
    }

    private fun createStatusCard(parent: LinearLayout, initialText: String): TextView {
        val tv = TextView(this).apply {
            text = initialText
            setTextColor(Color.LTGRAY)
            textSize = 14f
            setPadding(20, 20, 20, 10)
        }
        parent.addView(tv)
        return tv
    }

    private fun createButton(labelText: String, onClick: () -> Unit): Button {
        return Button(this).apply {
            text = labelText
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.parseColor("#2196F3"))
            setOnClickListener {
                vibrateFeedback(30L)
                onClick()
            }
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 20) }
            layoutParams = lp
        }
    }
}
