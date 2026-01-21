import platform
import os
from PySide6.QtCore import QUrl, QFileInfo
try:
    import winsound
except Exception:
    winsound = None

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAS_QT_MM = True
except ImportError:
    HAS_QT_MM = False

class AudioService:
    def __init__(self, config):
        self.config = config
        self.player = None
        self.audio_output = None
        if HAS_QT_MM:
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(1.0)

    def play_end(self):
        if not self.config.get("soundEnabled", True):
            return

        custom_path = self.config.get("customSoundPath", "")
        if custom_path and os.path.exists(custom_path) and HAS_QT_MM and self.player:
            try:
                self.player.stop()
                self.player.setSource(QUrl.fromLocalFile(custom_path))
                self.player.play()
                return
            except Exception:
                pass
        
        # Fallback to beep
        if platform.system() == "Windows" and winsound:
            try:
                winsound.Beep(800, 300)
            except Exception:
                pass
