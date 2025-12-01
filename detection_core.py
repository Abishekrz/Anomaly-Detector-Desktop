# detection_core.py

import os
import datetime
from pathlib import Path
from inference.detector import load_models
from inference.commenter import generate_comments
from utils.viz import draw_boxes
from openpyxl import Workbook, load_workbook

# Base directory (Desktop_App/)
BASE_DIR = Path(__file__).parent

# Load YOLO models ONCE globally
cfg, models = load_models()


# -------------------------------------------------------------
#  Create new session folder: sessions/YYYY-MM-DD_HH-MM-SS/
# -------------------------------------------------------------
def create_session_folder():
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session = BASE_DIR / "sessions" / now

    # Create subfolders
    (session / "uploads").mkdir(parents=True, exist_ok=True)
    (session / "results").mkdir(parents=True, exist_ok=True)

    print("\n===============================")
    print(" NEW SESSION:", session)
    print("===============================\n")

    return session


# -------------------------------------------------------------
# Save Excel results inside the session folder
# -------------------------------------------------------------
def save_to_excel(session_results_dir: Path, filename: str, detections: list, comments: list):
    excel_path = session_results_dir / "results.xlsx"

    # If exists → append; else → create new
    if excel_path.exists():
        wb = load_workbook(excel_path)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Results"
        ws.append(["Filename", "Detections", "Comments"])

    # Convert detection and comments to text
    labels = ", ".join([d.get("label", "") for d in detections]) if detections else "None"
    comment_text = "; ".join(comments) if comments else "No comments"

    ws.append([filename, labels, comment_text])
    wb.save(excel_path)

    print("EXCEL SAVED:", excel_path)


# -------------------------------------------------------------
# Main function: run YOLO models on image and produce results
# -------------------------------------------------------------
def run_inference_on_path(image_path: str, session_results_dir: Path):
    image_path = str(image_path).replace("\\", "/")
    print("\nINPUT IMAGE:", image_path)

    all_detections = []

    # ------------ Run each available model ------------- #
    for model_name, model_obj in models.items():
        print(f"\nRunning model '{model_name}' on image...")

        try:
            dets = model_obj.predict(image_path)
        except Exception as e:
            print(f"ERROR running model '{model_name}':", e)
            dets = []

        print(f"Model '{model_name}' detections:", len(dets))

        # Tag the model name into detection dict
        for d in dets:
            d["model"] = model_name

        all_detections.extend(dets)

    # ------------ Generate comments ------------ #
    comments = generate_comments(all_detections)

    # ------------ Save annotated image ------------ #
    out_name = f"annotated_{Path(image_path).name}"
    out_path = session_results_dir / out_name
    out_path_str = str(out_path).replace("\\", "/")

    print("OUTPUT FILE PATH:", out_path_str)

    try:
        draw_boxes(image_path, all_detections, out_path_str)
        print("ANNOTATION SAVED:", out_path_str)
    except Exception as e:
        print("DRAW ERROR:", e)

    # ------------ Save Excel ------------ #
    save_to_excel(session_results_dir, Path(image_path).name, all_detections, comments)

    return out_path_str, all_detections, comments


# -------------------------------------------------------------
# Basic folder structure creation
# -------------------------------------------------------------
def ensure_dirs():
    (BASE_DIR / "sessions").mkdir(exist_ok=True)
