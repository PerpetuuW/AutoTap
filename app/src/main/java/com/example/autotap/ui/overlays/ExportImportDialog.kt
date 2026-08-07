package com.example.autotap.ui.overlays

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Toast
import androidx.core.content.FileProvider
import com.example.autotap.MyAutoClickService
import com.example.autotap.R
import com.example.autotap.bindClickByNames
import com.example.autotap.logger.logDiagnostic
import com.example.autotap.logger.logError
import com.example.autotap.ui.base.OverlayBase
import com.example.autotap.ui.base.OverlayLayer
import com.example.autotap.ui.base.OverlayManager
import com.example.autotap.ui.base.OverlayPriority
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class ExportImportDialog(context: Context, overlayManager: OverlayManager) :
    OverlayBase(context, overlayManager) {

    init {
        gravity = Gravity.CENTER
        flags = WindowManager.LayoutParams.FLAG_DIM_BEHIND or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
        dimAmount = 0.6f
        layer = OverlayLayer.DIALOG_LAYER
        priority = OverlayPriority.CRITICAL
    }

    override fun createView(): View {
        val inflater = LayoutInflater.from(context)
        val view = inflater.inflate(R.layout.dialog_export_select, null)

        view.bindClickByNames("btnCloseExpSelect") {
            hide()
        }

        view.bindClickByNames("btnExpFullBackup", "btnExpSingleScript", "btnExpChainScripts", "btnExpTemplatesOnly") {
            exportFullBackupZip()
            hide()
        }

        return view
    }

    private fun exportFullBackupZip() {
        try {
            val filesDir = context.filesDir
            val timestamp = SimpleDateFormat("MMdd_HHmm", Locale.US).format(Date())
            val zipFile = File(filesDir, "autotap_backup_$timestamp.zip")

            val filesToZip = filesDir.listFiles { _, name ->
                name.endsWith(".json") || (name.startsWith("template_") && name.endsWith(".png"))
            } ?: emptyArray()

            if (filesToZip.isEmpty()) {
                Toast.makeText(context, "Нет сценариев или масок для экспорта!", Toast.LENGTH_SHORT).show()
                return
            }

            ZipOutputStream(FileOutputStream(zipFile)).use { zos ->
                for (file in filesToZip) {
                    FileInputStream(file).use { fis ->
                        val entry = ZipEntry(file.name)
                        zos.putNextEntry(entry)
                        fis.copyTo(zos)
                        zos.closeEntry()
                    }
                }
            }

            logDiagnostic("EXPORT", "Успешно создан ZIP-бэкап: ${zipFile.name} (${zipFile.length() / 1024} КБ)")

            val uri: Uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                zipFile
            )

            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }

            val chooser = Intent.createChooser(shareIntent, "Поделиться бэкапом AutoTap").apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(chooser)

        } catch (e: Exception) {
            logError("EXPORT", "Ошибка экспорта ZIP-бэкапа", e)
            Toast.makeText(context, "Ошибка создания бэкапа: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
}
