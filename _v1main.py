# main.py
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QCheckBox, QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from detection_core import run_inference_on_path, ensure_dirs
from inference.detector import load_models  # type: ignore

# We re-load cfg to get model names for UI
cfg, models = load_models()


class WorkerThread(QThread):
    one_done = pyqtSignal(str, list, list)  # out_path, detections, comments
    done = pyqtSignal()

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        for f in self.files:
            try:
                out, dets, comments = run_inference_on_path(f)
                self.one_done.emit(out, dets, comments)
            except Exception as e:
                self.one_done.emit("", [], [str(e)])
        self.done.emit()


class App(QWidget):
    def __init__(self):
        super().__init__()

        # state for browsing current batch
        self.current_results = []  # stores (out_path, detections, comments)
        self.current_index = 0
        self.all_logs = []  # store full batch logs here

        self.setWindowTitle("Annomaly Detector")
        self.setGeometry(100, 100, 1100, 720)
        ensure_dirs()

        # --- Widgets (create BEFORE layouts) ---
        # Left preview
        self.preview = QLabel("No image")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("border: 1px solid #ccc; background: #bbbbbbbb;")
        self.preview.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
    )


        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)

        # Logs list
        self.logs = QListWidget()

        # Buttons (these must be created before adding to button_row)
        self.btn_single = QPushButton("Select Single Image")
        self.btn_multi = QPushButton("Select Multiple Images")
        self.btn_open_excel = QPushButton("Open Results.xlsx")
        self.btn_prev = QPushButton("Previous Image")
        self.btn_next = QPushButton("Next Image")
        self.btn_browse_saved = QPushButton("Browse Saved Annotated Images")
        self.btn_view_all_logs = QPushButton("View Full Logs")

        # Model selection checkboxes container will be created later

        # --- Left button row (buttons under the image) ---
        self.button_row = QHBoxLayout()
        self.button_row.addWidget(self.btn_single)
        self.button_row.addWidget(self.btn_multi)
        self.button_row.addWidget(self.btn_open_excel)
        self.button_row.addWidget(self.btn_browse_saved)
        # Note: you may hide prev/next from this row if you prefer them on right
        self.button_row.addWidget(self.btn_prev)
        self.button_row.addWidget(self.btn_next)

        # --- Left layout (preview on top, buttons under it) ---
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.preview)  # image preview
        left_layout.addLayout(self.button_row)  # buttons under image
        left_layout.addWidget(self.progress)  # progress bar under buttons

        # --- Right: model checkboxes, logs and other controls ---
        self.model_checks = {}
        model_box = QVBoxLayout()
        model_box.addWidget(QLabel("Models to run:"))
        for mname in cfg["models"].keys():
            cb = QCheckBox(mname)
            cb.setChecked(True)
            self.model_checks[mname] = cb
            model_box.addWidget(cb)

        right_layout = QVBoxLayout()
        right_layout.addLayout(model_box)
        right_layout.addWidget(QLabel("Logs")) 
        right_layout.addWidget(self.logs) 
        right_layout.addWidget(self.progress) 
        right_layout.addWidget(self.btn_view_all_logs)
        # Add the main control buttons on the right as well (optional duplication)
        # right_layout.addWidget(self.btn_open_excel)
        # right_layout.addWidget(self.btn_browse_saved)
        # right_layout.addWidget(self.btn_prev)
        # right_layout.addWidget(self.btn_next)
        # right_layout.addWidget(QLabel("Logs"))
        # right_layout.addWidget(self.logs)
        # right_layout.addWidget(self.btn_view_all_logs)

        # --- Main layout ---
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

        # --- Connect signals ---
        self.btn_single.clicked.connect(self.open_single)
        self.btn_multi.clicked.connect(self.open_multi)
        self.btn_open_excel.clicked.connect(self.open_excel)
        self.btn_browse_saved.clicked.connect(self.browse_saved)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next.clicked.connect(self.next_image)
        self.btn_view_all_logs.clicked.connect(self.view_all_logs)

    # ------------- File selection and processing -------------
    def open_single(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if f:
            self.process_files([f])

    def open_multi(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg)")
        if files:
            self.process_files(files)

    def process_files(self, files):
        # Reset logs and browsing
        self.current_results = []
        self.all_logs = []
        self.current_index = 0

        # disable UI while running
        self.btn_single.setEnabled(False)
        self.btn_multi.setEnabled(False)
        self.logs.clear()

        upload_dir = Path(__file__).parent / "uploads"
        upload_dir.mkdir(exist_ok=True)

        saved_files = []

        import shutil

        for f in files:
            dest = upload_dir / Path(f).name
            dest = dest.as_posix()   # forward slashes for compatibility

            print("Saving uploaded file:", f, "→", dest)

            try:
                shutil.copy(f, dest)
                saved_files.append(dest)
            except Exception as e:
                print("Upload save error:", e)

        # Set progress bar
        self.progress.setVisible(True)
        self.progress.setMaximum(len(saved_files))
        self.progress.setValue(0)

        # Pass only saved copies into the worker
        self.thread = WorkerThread(saved_files)
        self.thread.one_done.connect(self.update_one)
        self.thread.done.connect(self.finish)
        self.thread.start()


    # ------------- Handling results -------------
    def update_one(self, out, detections, comments):
        # Store current result
        self.current_results.append((out, detections, comments))
        self.current_index = len(self.current_results) - 1

        # Append to global batch logs
        for c in comments:
            self.all_logs.append(c)

        # Show image
        if out and os.path.exists(out):
            try:
                pix = QPixmap(out.replace("\\", "/"))
                if not pix.isNull():
                    self.preview.setPixmap(
                        pix.scaled(
                            self.preview.width(),
                            self.preview.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )

                else:
                    self.preview.setText("Preview not available")
            except Exception:
                self.preview.setText("Preview error")
        else:
            self.preview.setText("No annotated image")

        # Show logs only for this image
        self.logs.clear()
        for c in comments:
            self.logs.addItem(QListWidgetItem(c))

        self.progress.setValue(self.progress.value() + 1)

    def finish(self):
        self.btn_single.setEnabled(True)
        self.btn_multi.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Complete", "Processing finished. results.xlsx updated in static/results.")

    # ------------- Utilities -------------
    def open_excel(self):
        path = Path(__file__).parent / "static" / "results" / "results.xlsx"
        if path.exists():
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform.startswith("darwin"):
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        else:
            QMessageBox.warning(self, "Not found", "Excel file not present yet. Run inference first.")

    def browse_saved(self):
        # Opens only annotated images inside static/results folder
        results_folder = Path(__file__).parent / "static" / "results"

        if not results_folder.exists():
            QMessageBox.warning(self, "No Results", "No annotated images found yet.")
            return

        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Annotated Image",
            str(results_folder),
            "Images (*.png *.jpg *.jpeg)"
        )

        if file:
            file = file.replace("\\", "/")
            pix = QPixmap(file)
            if not pix.isNull():
                self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio))
                self.logs.addItem(QListWidgetItem(f"Opened saved image: {file}"))
            else:
                QMessageBox.warning(self, "Preview error", "Could not load the selected image.")

    # ------------- Batch browsing (prev/next) -------------
    def show_image_by_index(self):
        if not self.current_results:
            return

        out, dets, comments = self.current_results[self.current_index]
        if out and os.path.exists(out):
            pix = QPixmap(out.replace("\\", "/"))
            if not pix.isNull():
                self.preview.setPixmap(
                    pix.scaled(
                        self.preview.width(),
                        self.preview.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
                    
            else:
                self.preview.setText("Preview not available")
        else:
            self.preview.setText("No annotated image")

        # Clear logs and show only this image’s logs
        self.logs.clear()
        for c in comments:
            self.logs.addItem(QListWidgetItem(c))

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image_by_index()
        else:
            QMessageBox.information(self, "Info", "Already at the first image.")

    def next_image(self):
        if self.current_index < len(self.current_results) - 1:
            self.current_index += 1
            self.show_image_by_index()
        else:
            QMessageBox.information(self, "Info", "Already at the last image.")

    # ------------- View all logs -------------
    def view_all_logs(self):
        if not self.all_logs:
            QMessageBox.information(self, "No Logs", "No logs available yet.")
            return

        # Create popup window
        log_window = QWidget()
        log_window.setWindowTitle("Full Logs")
        log_window.setGeometry(300, 200, 600, 500)

        layout = QVBoxLayout()

        list_widget = QListWidget()
        for log in self.all_logs:
            list_widget.addItem(QListWidgetItem(log))

        layout.addWidget(list_widget)
        log_window.setLayout(layout)

        # Show window
        log_window.show()

        # Keep a reference so it's not garbage-collected
        self.log_window_ref = log_window
    def resizeEvent(self, event):
        if self.preview.pixmap():
            self.preview.setPixmap(
                self.preview.pixmap().scaled(
                    self.preview.width(),
                    self.preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        return super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())
