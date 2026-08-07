package com.example.autotap.service

import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import android.widget.Toast
import androidx.annotation.RequiresApi
import com.example.autotap.MainActivity
import com.example.autotap.MyAutoClickService

@RequiresApi(Build.VERSION_CODES.N)
class QuickTileService : TileService() {

    override fun onStartListening() {
        super.onStartListening()
        updateTileState()
    }

    override fun onClick() {
        super.onClick()
        val svc = MyAutoClickService.instance
        if (svc != null) {
            svc.showControlPanel()
            Toast.makeText(this, "Панель AutoTap запущен!", Toast.LENGTH_SHORT).show()
        } else {
            val intent = Intent(this, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivityAndCollapse(intent)
        }
        updateTileState()
    }

    private fun updateTileState() {
        val tile = qsTile ?: return
        val isActive = MyAutoClickService.instance != null
        tile.state = if (isActive) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        tile.label = if (isActive) "AutoTap: ВКЛ" else "AutoTap: ВЫКЛ"
        tile.updateTile()
    }
}
