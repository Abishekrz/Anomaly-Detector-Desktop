# inference/detector.py
from ultralytics import YOLO
import os

def load_models():
    cfg = {
        "models": {
            "fire": {"path": "models/fire_model.pt"},
            "textile": {"path": "models/textile_model.pt"},
            "panel": {"path": "models/electrical_panel.pt"},

            # Correct name for PPE model
            "ppe": {"path": "models/ppe_model.pt"}
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
