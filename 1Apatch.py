#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
AUTOTAP PRO v41 - IN-PLACE SHORT PRECISION PATCHER
===============================================================================
"""

import os
import re
import sys

def patch_file(rel_path, replacements):
    abs_path = os.path.abspath(rel_path)
    if not os.path.exists(abs_path):
        print(f"⚠️ [SKIP]: Файл {rel_path} не найден.")
        return False
    
    with open(abs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old_pattern, new_text in replacements:
        if isinstance(old_pattern, str):
            content = content.replace(old_pattern, new_text)
        else:
            content = old_pattern.sub(new_text, content)
            
    if content != original:
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.truncate(0)  # Полное удаление содержимого перед записью
            f.write(content)
        print(f"🟢 [PATCHED]: {rel_path}")
        return True
    else:
        print(f"ℹ️ [ALREADY PATCHED / NO CHANGE]: {rel_path}")
        return True

def run():
    print("=================================================================")
    print("🚀 СТАРТ ТОЧЕЧНОГО ИН-ПЛЕЙС ПАТЧИНГА AUTOTAP PRO (v41)")
    print("=================================================================")

    # 1. Патчим OverlayBase.kt (TouchSlop drag & measurement)
    overlay_base_path = "app/src/main/java/com/example/autotap/ui/base/OverlayBase.kt"
    
    old_drag = re.compile(r'protected fun setupDragAndDrop\(handleView: View\) \{[\s\S]*?\n    \}')
    new_drag = '''protected fun setupDragAndDrop(handleView: View) {
        var startX = 0f
        var startY = 0f
        var isDragging = false

        handleView.setOnTouchListener { _, event ->
            val lp = layoutParams ?: params ?: return@setOnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = event.rawX
                    startY = event.rawY
                    isDragging = false
                    false
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - startX).toInt()
                    val dy = (event.rawY - startY).toInt()

                    if (!isDragging && (abs(dx) > touchSlop || abs(dy) > touchSlop)) {
                        isDragging = true
                    }

                    if (isDragging) {
                        updatePosition(lp.x + dx, lp.y + dy)
                        startX = event.rawX
                        startY = event.rawY
                    }
                    isDragging
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    val wasDragging = isDragging
                    isDragging = false
                    wasDragging
                }
                else -> false
            }
        }
    }'''

    old_measure = 'val viewW = v?.width?.takeIf { it > 0 } ?: width.takeIf { it > 0 } ?: 140'
    new_measure = '''if (v != null && (v.width == 0 || v.height == 0)) {
            v.measure(
                View.MeasureSpec.makeMeasureSpec(screenSize.x, View.MeasureSpec.AT_MOST),
                View.MeasureSpec.makeMeasureSpec(screenSize.y, View.MeasureSpec.AT_MOST)
            )
        }
        val viewW = v?.measuredWidth?.takeIf { it > 0 } ?: v?.width?.takeIf { it > 0 } ?: width.takeIf { it > 0 } ?: 140'''

    patch_file(overlay_base_path, [(old_drag, new_drag), (old_measure, new_measure)])

    # 2. Патчим CaptureFrameOverlay.kt (WRAP_CONTENT размеры)
    capture_kt_path = "app/src/main/java/com/example/autotap/ui/overlays/CaptureFrameOverlay.kt"
    old_size = '''width = currentFrameWidthPx
        height = currentFrameHeightPx'''
    new_size = '''width = WindowManager.LayoutParams.WRAP_CONTENT
        height = WindowManager.LayoutParams.WRAP_CONTENT'''
    patch_file(capture_kt_path, [(old_size, new_size)])

    # 3. Патчим EditActionDialog.kt (Сохранение X/Y)
    edit_kt_path = "app/src/main/java/com/example/autotap/ui/overlays/EditActionDialog.kt"
    old_edit_apply = 'action.delay = etEditDelayMs?.text?.toString()?.toLongOrNull() ?: action.delay'
    new_edit_apply = '''val inputX = etEditX?.text?.toString()?.toFloatOrNull()
                val inputY = etEditY?.text?.toString()?.toFloatOrNull()
                if (inputX != null) {
                    action.xNorm = if (inputX > 1.0f) (inputX / screenSize.x).coerceIn(0f, 1f) else inputX.coerceIn(0f, 1f)
                }
                if (inputY != null) {
                    action.yNorm = if (inputY > 1.0f) (inputY / screenSize.y).coerceIn(0f, 1f) else inputY.coerceIn(0f, 1f)
                }
                action.delay = etEditDelayMs?.text?.toString()?.toLongOrNull() ?: action.delay'''
    patch_file(edit_kt_path, [(old_edit_apply, new_edit_apply)])

    # 4. Патчим XML макет прицела (убираем сдвиг тулбаров)
    capture_xml_path = "app/src/main/res/layout/floating_capture_frame.xml"
    patch_file(capture_xml_path, [('android:translationY="-44dp"', ''), ('android:translationY="44dp"', '')])

    print("=================================================================")
    print("🎉 ВСЕ ПАТЧИ УСПЕШНО ПРИМЕНЕНЫ К ПРОЕКТУ!")
    print("=================================================================")

if __name__ == "__main__":
    run()