import os
import sys
from PySide6.QtGui import QPixmap

if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def load_skin(skin_id):
    if os.path.isabs(skin_id):
        base = skin_id
    else:
        base = os.path.join(ROOT, "skins", skin_id)
        
    frames = []
    seq = []
    try:
        if os.path.exists(base):
            for name in os.listdir(base):
                if name.lower().startswith("skin_") and name.lower().endswith(".png"):
                    seq.append(name)
    except Exception:
        pass

    if seq:
        for name in sorted(seq):
            p = QPixmap(os.path.join(base, name))
            if p.isNull() or p.width() != 256 or p.height() != 256:
                continue
            frames.append(p)
        if frames:
            return frames, True, _load_meta(base)

    # Try single frame skin.png
    single_path = os.path.join(base, "skin.png")
    if os.path.exists(single_path):
        p = QPixmap(single_path)
        if not p.isNull() and p.width() == 256 and p.height() == 256:
            return [p], False, _load_meta(base)
            
    # Raise exception if no valid skin found, caller should handle fallback
    raise ValueError(f"No valid 256x256 skin found in {base}")

def _load_meta(base_path):
    import json
    meta_path = os.path.join(base_path, "skin.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}
