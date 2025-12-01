# main.py
import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QMessageBox,
    QCheckBox,
    QSizePolicy,
    QScrollArea,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from detection_core import run_inference_on_path, ensure_dirs, create_session_folder, cfg


# ---------------- Worker Thread ---------------- #
class WorkerThread(QThread):
    one_done = pyqtSignal(str, list, list)
    done = pyqtSignal()

    def __init__(self, files, session_results_dir):
        super().__init__()
        self.files = files
        self.session_results_dir = session_results_dir

    def run(self):
        for f in self.files:
            try:
                out, dets, comments = run_inference_on_path(f, self.session_results_dir)
                self.one_done.emit(out, dets, comments)
            except Exception as e:
                self.one_done.emit("", [], [f"Error: {e}"])
        self.done.emit()


# ---------------- Application UI ---------------- #
class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Annomaly Detector")
        self.resize(1200, 700)
        self.setMinimumSize(600, 400)

        ensure_dirs()

        self.session_folder = None
        self.upload_dir = None
        self.results_dir = None

        self.current_results = []
        self.current_index = 0
        self.all_logs = []

        # ---------------- LEFT (Image + buttons) ---------------- #

        self.preview = QLabel("No image")
        self.preview.setStyleSheet("border: 1px solid #ccc; background: #fafafa;")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.progress = QProgressBar()
        self.progress.setVisible(False)

        # Buttons
        self.btn_single = QPushButton("Select Single Image")
        self.btn_multi = QPushButton("Select Multiple Images")
        self.btn_prev = QPushButton("Previous Image")
        self.btn_next = QPushButton("Next Image")

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_single)
        btn_row.addWidget(self.btn_multi)
        btn_row.addWidget(self.btn_prev)
        btn_row.addWidget(self.btn_next)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.preview, stretch=5)
        left_layout.addLayout(btn_row)
        left_layout.addWidget(self.progress)

        # ---------------- RIGHT (Models + logs) ---------------- #

        self.model_checks = {}
        model_layout = QVBoxLayout()
        model_layout.addWidget(QLabel("Models to Run:"))

        for mname in cfg["models"].keys():
            cb = QCheckBox(mname)
            cb.setChecked(True)
            self.model_checks[mname] = cb
            model_layout.addWidget(cb)

        model_widget = QWidget()
        model_widget.setLayout(model_layout)

        model_scroll = QScrollArea()
        model_scroll.setWidgetResizable(True)
        model_scroll.setWidget(model_widget)

        self.logs = QListWidget()
        self.logs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.btn_open_excel = QPushButton("Open Results.xlsx")
        self.btn_browse_saved = QPushButton("Browse Saved Annotated Images")
        self.btn_view_logs = QPushButton("View Full Logs")

        right_layout = QVBoxLayout()
        right_layout.addWidget(model_scroll)
        right_layout.addWidget(self.btn_open_excel)
        right_layout.addWidget(self.btn_browse_saved)
        right_layout.addWidget(QLabel("Logs"))
        right_layout.addWidget(self.logs, stretch=1)
        right_layout.addWidget(self.btn_view_logs)
        right_layout.addStretch()

        # ---------------- Main Layout ---------------- #
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

        # ---------------- Connections ---------------- #
        self.btn_single.clicked.connect(self.open_single)
        self.btn_multi.clicked.connect(self.open_multi)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next.clicked.connect(self.next_image)
        self.btn_open_excel.clicked.connect(self.open_excel)
        self.btn_browse_saved.clicked.connect(self.browse_saved)
        self.btn_view_logs.clicked.connect(self.view_all_logs)

    # ------------------------------------------------------------
    # File Selection & Session Handling
    # ------------------------------------------------------------
    def open_single(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if f:
            self.start_new_session([f])

    def open_multi(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg)")
        if files:
            self.start_new_session(files)

    def start_new_session(self, files):
        # Create session folder
        self.session_folder = create_session_folder()
        self.upload_dir = self.session_folder / "uploads"
        self.results_dir = self.session_folder / "results"

        self.current_results = []
        self.current_index = 0
        self.all_logs = []
        self.logs.clear()

        # Copy files into session/uploads/
        saved_files = []
        import shutil

        for f in files:
            dest = self.upload_dir / Path(f).name
            try:
                shutil.copy(f, dest)
                saved_files.append(dest.as_posix())
                print("Saved upload:", f, "→", dest)
            except Exception as e:
                print("Error copying:", e)

        # Run detection
        self.progress.setVisible(True)
        self.progress.setMaximum(len(saved_files))
        self.progress.setValue(0)

        self.thread = WorkerThread(saved_files, self.results_dir)
        self.thread.one_done.connect(self.update_result)
        self.thread.done.connect(self.finish_session)
        self.thread.start()

    # ------------------------------------------------------------
    # Per-image updates
    # ------------------------------------------------------------
    def update_result(self, out, detections, comments):
        self.current_results.append((out, detections, comments))
        self.current_index = len(self.current_results) - 1

        if out and os.path.exists(out):
            pix = QPixmap(out)
            self.preview.setPixmap(
                pix.scaled(
                    self.preview.width(),
                    self.preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        self.logs.clear()
        for c in comments:
            self.logs.addItem(QListWidgetItem(c))
            self.all_logs.append(c)

        self.progress.setValue(self.progress.value() + 1)

    # ------------------------------------------------------------
    # After batch is finished
    # ------------------------------------------------------------
    def finish_session(self):
        self.progress.setVisible(False)
        QMessageBox.information(self, "Complete", "Batch processing finished!")

    # ------------------------------------------------------------
    # Browsing results
    # ------------------------------------------------------------
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def next_image(self):
        if self.current_index < len(self.current_results) - 1:
            self.current_index += 1
            self.show_current_image()

    def show_current_image(self):
        out, dets, comments = self.current_results[self.current_index]
        if out and os.path.exists(out):
            pix = QPixmap(out)
            self.preview.setPixmap(
                pix.scaled(
                    self.preview.width(),
                    self.preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        self.logs.clear()
        for c in comments:
            self.logs.addItem(QListWidgetItem(c))

    # ------------------------------------------------------------
    # Open Excel
    # ------------------------------------------------------------
    def open_excel(self):
        if self.results_dir is None:
            return

        excel_file = self.results_dir / "results.xlsx"
        if excel_file.exists():
            os.startfile(excel_file)
        else:
            QMessageBox.warning(self, "Not Found", "No Excel file in this session.")

    # ------------------------------------------------------------
    # Browse saved annotated images
    # ------------------------------------------------------------
    def browse_saved(self):
        if self.results_dir is None:
            return

        file, _ = QFileDialog.getOpenFileName(
            self, "Open Annotated Image", str(self.results_dir), "Images (*.png *.jpg *.jpeg)"
        )
        if file:
            pix = QPixmap(file)
            self.preview.setPixmap(
                pix.scaled(
                    self.preview.width(),
                    self.preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    # ------------------------------------------------------------
    # View full logs
    # ------------------------------------------------------------
    def view_all_logs(self):
        if not self.all_logs:
            QMessageBox.information(self, "Logs", "No logs yet.")
            return

        log_window = QWidget()
        log_window.setWindowTitle("Full Logs")
        log_window.resize(500, 600)

        layout = QVBoxLayout()
        lst = QListWidget()

        for log in self.all_logs:
            lst.addItem(QListWidgetItem(log))

        layout.addWidget(lst)
        log_window.setLayout(layout)
        log_window.show()

        self.log_window_ref = log_window

    # ------------------------------------------------------------
    # Resize event for responsive preview
    # ------------------------------------------------------------
    def resizeEvent(self, event):
        if self.preview.pixmap():
            self.preview.setPixmap(
                self.preview.pixmap().scaled(
                    self.preview.width(),
                    self.preview.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        return super().resizeEvent(event)


# ---------------- START APP ---------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
