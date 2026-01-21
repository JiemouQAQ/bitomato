import json
import os

class ConfigService:
    PATH = os.path.join(os.getcwd(), "config.json")
    DEFAULTS = {
        "workMinutes": 25,
        "shortBreakMinutes": 5,
        "longBreakMinutes": 15,
        "sessionsBeforeLongBreak": 4,
        "skinId": "default",
        "frameRate": 8,
        "frameDuration": 100,
        "uiScale": 1,
        "alwaysOnTop": True,
        "soundEnabled": False,
        "manualBreak": False,
        "countUpMode": False,
        "autoBackup": False,
        "customSoundPath": "",
        "textColor": "#FFFFFF",
        "textOutlineEnabled": False,
        "textOutlineColor": "#000000",
        "textOutlineWidth": 2,
        "language": "zh-CN"
    }

    @classmethod
    def ensure_defaults(cls):
        if not os.path.exists(cls.PATH):
            with open(cls.PATH, "w", encoding="utf-8") as f:
                json.dump(cls.DEFAULTS, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls):
        try:
            with open(cls.PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = dict(cls.DEFAULTS)
        for k, v in cls.DEFAULTS.items():
            if k not in data:
                data[k] = v
        for k in ("workMinutes", "shortBreakMinutes"):
            try:
                val = int(data.get(k, cls.DEFAULTS[k]))
            except Exception:
                val = cls.DEFAULTS[k]
            
            min_val = 2 if k == "workMinutes" else 1
            if val < min_val:
                val = min_val
            if val > 99:
                val = 99
            data[k] = val
        try:
            fd = int(data.get("frameDuration", cls.DEFAULTS["frameDuration"]))
        except Exception:
            fd = cls.DEFAULTS["frameDuration"]
        if fd < 100:
            fd = 100
        if fd > 1000:
            fd = 1000
        data["frameDuration"] = fd
        return data

    @classmethod
    def save(cls, data):
        with open(cls.PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
