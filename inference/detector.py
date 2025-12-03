# inference/detector.py
from ultralytics import YOLO
import os, sys


def resource_path(relative_path):
    """Get absolute path for PyInstaller EXE or normal Python."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_models():
    cfg = {
        "models": {
            "fire": {"path": resource_path("models/fire_model.pt")},
            "textile": {"path": resource_path("models/textile_model.pt")},
            "panel": {"path": resource_path("models/electrical_panel.pt")},
            "ppe": {"path": resource_path("models/ppe_model.pt")},
        }
    }

    loaded = {}

    for name, meta in cfg["models"].items():
        path = meta["path"]

        if not os.path.exists(path):
            print(f"⚠ WARNING: Model not found: {path}")
            continue

        print(f"[detector] Loading model '{name}' from {path}")
        loaded[name] = YOLO(path)

    return cfg, loaded
