import json
import os
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

class StatsService:
    PATH = os.path.join(ROOT, "stats.json")

    def __init__(self):
        self.data = {
            "total_focus_seconds": 0,
            "total_focus_sessions": 0,
            "bucket_seconds": {
                "midnight": 0,   # 00:00-06:00
                "morning": 0,    # 06:00-12:00
                "afternoon": 0,  # 12:00-18:00
                "evening": 0     # 18:00-24:00
            }
        }
        self._load()
        self._unsaved_seconds = 0

    def _load(self):
        if os.path.exists(self.PATH):
            try:
                with open(self.PATH, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def _save(self):
        try:
            with open(self.PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_work_seconds(self, seconds: int, now: datetime | None = None):
        if seconds <= 0:
            return
        self.data["total_focus_seconds"] += seconds
        self._unsaved_seconds += seconds
        dt = now or datetime.now()
        h = dt.hour
        if 0 <= h < 6:
            key = "midnight"
        elif 6 <= h < 12:
            key = "morning"
        elif 12 <= h < 18:
            key = "afternoon"
        else:
            key = "evening"
        self.data["bucket_seconds"][key] += seconds
        if self._unsaved_seconds >= 60:
            self._save()
            self._unsaved_seconds = 0

    def increment_session(self):
        self.data["total_focus_sessions"] += 1
        self._save()

    def get_summary(self):
        seconds = int(self.data.get("total_focus_seconds", 0))
        sessions = int(self.data.get("total_focus_sessions", 0))
        buckets = dict(self.data.get("bucket_seconds", {}))
        favorites = []
        if seconds > 0 and sessions > 5:
            for key in ("midnight", "morning", "afternoon", "evening"):
                share = buckets.get(key, 0) / seconds
                if share > 0.5:
                    favorites.append(key)
        return {
            "total_focus_seconds": seconds,
            "total_focus_sessions": sessions,
            "bucket_seconds": buckets,
            "favorite_slots": favorites
        }

    def flush(self):
        if self._unsaved_seconds > 0:
            self._save()
            self._unsaved_seconds = 0

    def import_data(self, new_data: dict):
        """
        Import data from backup.
        Expects keys: total_focus_seconds, total_focus_sessions, bucket_seconds
        """
        if not isinstance(new_data, dict):
            return False
        
        # Basic validation
        req_keys = ["total_focus_seconds", "total_focus_sessions", "bucket_seconds"]
        for k in req_keys:
            if k not in new_data:
                return False
        
        # Update and save
        self.data = new_data
        self._save()
        return True

    def clear_data(self):
        """Reset all statistical data to zero/empty."""
        self.data = {
            "total_focus_seconds": 0,
            "total_focus_sessions": 0,
            "bucket_seconds": {
                "midnight": 0,   # 00:00-06:00
                "morning": 0,    # 06:00-12:00
                "afternoon": 0,  # 12:00-18:00
                "evening": 0     # 18:00-24:00
            }
        }
        self._save()
