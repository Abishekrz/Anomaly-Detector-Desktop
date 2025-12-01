# tests/test_detector.py
import pytest
from inference.detector import load_models# type: ignore

def test_load_models():
    cfg, models = load_models()
    assert isinstance(cfg, dict)
    assert isinstance(models, dict)
    # each entry should have a name and ModelWrapper object
    for name, mw in models.items():
        assert hasattr(mw, "predict")
        # assert callable(mw.predict)