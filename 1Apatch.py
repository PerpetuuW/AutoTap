import os

def write_file(rel_path, content):
    parts = rel_path.split("/")
    full_path = os.path.join(*parts)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Обновлен модуль: {rel_path}")

def fix_adapt_mask_reference():
    print("🚀 Добавление метода adaptMask в MaskCalibrator v37.4.0-PRO...")

    # 1. app/build.gradle.kts
    gradle_code = r"""plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.autotap"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.autotap"
        minSdk = 24
        targetSdk = 35
        versionCode = 2540
        versionName = "37.4.0-PRO"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("com.google.android.material:material:1.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
"""
    write_file("app/build.gradle.kts", gradle_code)

    # 2. MaskCalibrator.kt (Добавлен метод adaptMask)
    calibrator_code = r"""package com.example.autotap.engine

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.PointF
import android.graphics.Rect
import com.example.autotap.data.TemplateMetadata
import kotlin.math.max
import kotlin.math.min

data class CalibratedMask(
    val originalMask: Bitmap,
    val downscaledMask: Bitmap,
    val downscaledFrame: Bitmap,
    val multiScaleMasks: List<Pair<Float, Bitmap>>,
    val contourPoints: List<PointF>,
    val metadata: TemplateMetadata
)

object MaskCalibrator {

    fun calibrateMask(
        bitmap: Bitmap,
        frame: Bitmap,
        sourceDpi: Int = 480,
        targetDpi: Int = 480,
        isCircle: Boolean = true
    ): CalibratedMask {
        val claheMask = applyClaheLocalContrast(bitmap)
        val downMask = Bitmap.createScaledBitmap(claheMask, (claheMask.width * 0.5f).toInt().coerceAtLeast(1), (claheMask.height * 0.5f).toInt().coerceAtLeast(1), true)
        val downFrame = Bitmap.createScaledBitmap(frame, (frame.width * 0.5f).toInt().coerceAtLeast(1), (frame.height * 0.5f).toInt().coerceAtLeast(1), true)

        val multiScale = listOf(
            Pair(1.0f, claheMask),
            Pair(0.75f, Bitmap.createScaledBitmap(claheMask, (claheMask.width * 0.75f).toInt().coerceAtLeast(1), (claheMask.height * 0.75f).toInt().coerceAtLeast(1), true)),
            Pair(0.5f, downMask)
        )

        val contour = extractContour(claheMask)

        val metadata = TemplateMetadata(
            width = bitmap.width,
            height = bitmap.height,
            dpi = targetDpi,
            scale = 1.0f,
            boundingBox = Rect(0, 0, bitmap.width, bitmap.height),
            isCircleShape = isCircle
        )

        return CalibratedMask(
            originalMask = claheMask,
            downscaledMask = downMask,
            downscaledFrame = downFrame,
            multiScaleMasks = multiScale,
            contourPoints = contour,
            metadata = metadata
        )
    }

    fun adaptMask(bmp: Bitmap): Bitmap {
        return applyClaheLocalContrast(bmp)
    }

    fun applyClaheLocalContrast(bmp: Bitmap): Bitmap {
        val out = bmp.copy(Bitmap.Config.ARGB_8888, true)
        val w = out.width
        val h = out.height
        val pixels = IntArray(w * h)
        out.getPixels(pixels, 0, w, 0, 0, w, h)

        for (i in pixels.indices) {
            val c = pixels[i]
            val r = Color.red(c)
            val g = Color.green(c)
            val b = Color.blue(c)
            val alpha = Color.alpha(c)

            val gray = (0.299f * r + 0.587f * g + 0.114f * b).toInt().coerceIn(0, 255)
            val enhanced = if (gray > 128) max(0, gray - 15) else minOf(255, gray + 15)
            pixels[i] = Color.argb(alpha, enhanced, enhanced, enhanced)
        }

        out.setPixels(pixels, 0, w, 0, 0, w, h)
        return out
    }

    private fun extractContour(bmp: Bitmap): List<PointF> {
        val list = ArrayList<PointF>()
        val w = bmp.width
        val h = bmp.height
        for (y in 0 until h step 4) {
            for (x in 0 until w step 4) {
                val alpha = Color.alpha(bmp.getPixel(x, y))
                if (alpha > 128) {
                    list.add(PointF(x.toFloat(), y.toFloat()))
                }
            }
        }
        return list
    }
}
"""
    write_file("app/src/main/java/com/example/autotap/engine/MaskCalibrator.kt", calibrator_code)

    print("✨ Метод adaptMask успешно добавлен в MaskCalibrator!")

if __name__ == "__main__":
    fix_adapt_mask_reference()