# inference/detector.py
from ultralytics import YOLO
import os

def load_models():
    cfg = {
        "models": {
            "fire":  {"path": "models/fire_model.pt"},
            "textile": {"path": "models/textile_model.pt"},
            "panel": {"path": "models/electrical_panel.pt"},
        }
    }

    loaded = {}

    for name, meta in cfg["models"].items():
        path = meta["path"]

        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")

        print(f"[detector] Loading model '{name}' from {path}")
        loaded[name] = YOLO(path)

    return cfg, loaded
