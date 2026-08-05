package com.example.autotap.ui

import android.annotation.SuppressLint
import android.content.Context
import android.os.Build
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.ImageButton
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import com.example.autotap.*
import com.example.autotap.core.AutoTapAccessibilityService
import com.example.autotap.data.ActionType
import com.example.autotap.data.AutoTapAction
import com.example.autotap.data.ScenarioManager

class OverlayManager(
    private val context: Context,
    private val scenarioManager: ScenarioManager,
    private val onStartClick: () -> Unit,
    private val onStopClick: () -> Unit
) {
    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var controlPanelContainer: View? = null
    private val targetPointViews = mutableListOf<View>()
    private var isPlaying = false

    @SuppressLint("InflateParams", "ClickableViewAccessibility")
    fun showOverlay() {
        if (controlPanelContainer != null) return

        val inflater = LayoutInflater.from(context)
        controlPanelContainer = inflater.inflate(R.layout.layout_floating_control_bar, null)

        val btnPlayPause = controlPanelContainer!!.findViewById<ImageButton>(R.id.btnPlayPause)
        val btnAddPoint = controlPanelContainer!!.findViewById<ImageButton>(R.id.btnAddPoint)
        val btnRemovePoint = controlPanelContainer!!.findViewById<ImageButton>(R.id.btnRemovePoint)

        btnPlayPause.setOnClickListener {
            isPlaying = !isPlaying
            if (isPlaying) {
                btnPlayPause.setImageResource(R.drawable.ic_stop)
                onStartClick()
            } else {
                btnPlayPause.setImageResource(R.drawable.ic_play)
                onStopClick()
            }
        }

        btnAddPoint.setOnClickListener { addTargetPoint() }
        btnRemovePoint.setOnClickListener { removeTargetPoint() }

        val params = context.createOverlayParams().apply {
            x = 50
            y = 300
        }

        setupDragTouchListener(controlPanelContainer!!, params)
        windowManager.safeAddView(controlPanelContainer!!, params)
    }

    @SuppressLint("InflateParams", "SetTextI18n")
    private fun addTargetPoint() {
        val inflater = LayoutInflater.from(context)
        val targetView = inflater.inflate(R.layout.layout_target_point, null)
        val tvNumber = targetView.findViewById<TextView>(R.id.tvTargetNumber)

        val index = targetPointViews.size + 1
        tvNumber.text = index.toString()

        val screenSize = context.getRealScreenSize()
        val defaultX = screenSize.x / 2 - 24.dpToPx
        val defaultY = screenSize.y / 3 + (index * 60.dpToPx)

        val action = AutoTapAction(
            index = index,
            x = defaultX + 24.dpToPx,
            y = defaultY + 24.dpToPx
        )
        scenarioManager.addAction(action)

        val params = context.createOverlayParams().apply {
            x = defaultX
            y = defaultY
        }

        setupTargetListeners(targetView, params, action)
        windowManager.safeAddView(targetView, params)
        targetPointViews.add(targetView)
    }

    private fun removeTargetPoint() {
        if (targetPointViews.isNotEmpty()) {
            val lastView = targetPointViews.removeAt(targetPointViews.size - 1)
            windowManager.safeRemoveView(lastView)
            scenarioManager.removeLastAction()
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupTargetListeners(view: View, params: WindowManager.LayoutParams, action: AutoTapAction) {
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f
        var isClick = true

        view.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    isClick = true
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val diffX = (event.rawX - initialTouchX).toInt()
                    val diffY = (event.rawY - initialTouchY).toInt()
                    if (Math.abs(diffX) > 5 || Math.abs(diffY) > 5) {
                        isClick = false
                    }
                    params.x = initialX + diffX
                    params.y = initialY + diffY
                    windowManager.safeUpdateViewLayout(view, params)
                    action.x = params.x + 24.dpToPx
                    action.y = params.y + 24.dpToPx
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (isClick) {
                        showActionEditDialog(action)
                    }
                    true
                }
                else -> false
            }
        }
    }

    @SuppressLint("InflateParams", "SetTextI18n")
    private fun showActionEditDialog(action: AutoTapAction) {
        val inflater = LayoutInflater.from(context)
        val dialogView = inflater.inflate(R.layout.dialog_edit_action, null)

        val tvTitle = dialogView.findViewById<TextView>(R.id.tvDialogTitle)
        val spType = dialogView.findViewById<Spinner>(R.id.spActionType)
        val etDuration = dialogView.findViewById<EditText>(R.id.etDuration)
        val etDelay = dialogView.findViewById<EditText>(R.id.etDelay)
        val etColor = dialogView.findViewById<EditText>(R.id.etTargetColor)
        val etTolerance = dialogView.findViewById<EditText>(R.id.etTolerance)
        val btnSample = dialogView.findViewById<Button>(R.id.btnSampleColor)
        val btnSave = dialogView.findViewById<Button>(R.id.btnSaveAction)
        val btnCancel = dialogView.findViewById<Button>(R.id.btnCancel)

        tvTitle.text = "Настройка действия #${action.index}"
        etDuration.setText(action.durationMs.toString())
        etDelay.setText(action.delayAfterMs.toString())
        etColor.setText(action.targetColorHex)
        etTolerance.setText(action.colorTolerance.toString())

        val adapter = ArrayAdapter(context, android.R.layout.simple_spinner_item, ActionType.values().map { it.name })
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spType.adapter = adapter
        spType.setSelection(action.type.ordinal)

        val dialogParams = context.createOverlayParams().apply {
            width = WindowManager.LayoutParams.MATCH_PARENT
            height = WindowManager.LayoutParams.WRAP_CONTENT
        }

        btnSample.setOnClickListener {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val service = AutoTapAccessibilityService.instance
                if (service != null) {
                    service.captureScreenBitmap().thenAccept { bitmap ->
                        if (bitmap != null) {
                            val sampledHex = service.samplePixelColor(bitmap, action.x, action.y)
                            etColor.post {
                                etColor.setText(sampledHex)
                                Toast.makeText(context, "Снят цвет: $sampledHex", Toast.LENGTH_SHORT).show()
                            }
                            bitmap.recycle()
                        }
                    }
                } else {
                    Toast.makeText(context, "Accessibility Service не активен", Toast.LENGTH_SHORT).show()
                }
            } else {
                Toast.makeText(context, "Требуется Android 11+", Toast.LENGTH_SHORT).show()
            }
        }

        btnSave.setOnClickListener {
            action.type = ActionType.values()[spType.selectedItemPosition]
            action.durationMs = etDuration.text.toString().toLongOrNull() ?: 100L
            action.delayAfterMs = etDelay.text.toString().toLongOrNull() ?: 500L
            action.targetColorHex = etColor.text.toString()
            action.colorTolerance = etTolerance.text.toString().toIntOrNull() ?: 15
            scenarioManager.saveScenarioAtomic()
            windowManager.safeRemoveView(dialogView)
            Toast.makeText(context, "Шаблон #${action.index} сохранен", Toast.LENGTH_SHORT).show()
        }

        btnCancel.setOnClickListener {
            windowManager.safeRemoveView(dialogView)
        }

        windowManager.safeAddView(dialogView, dialogParams)
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupDragTouchListener(view: View, params: WindowManager.LayoutParams) {
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f

        view.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    params.x = initialX + (event.rawX - initialTouchX).toInt()
                    params.y = initialY + (event.rawY - initialTouchY).toInt()
                    windowManager.safeUpdateViewLayout(view, params)
                    true
                }
                else -> false
            }
        }
    }
}
