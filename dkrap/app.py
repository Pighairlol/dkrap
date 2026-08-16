from pathlib import Path
import sys
from PySide6 import QtCore, QtWidgets
from .analyzer import analyze_files
from .generator import generate
from .models import Library
from .audio import write_wav

APP_NAME = "DK Rap Vocal Builder"
APP_DIR = Path.home() / ".dkrap_vocal_builder"
LIB_PATH = APP_DIR / "library.json"

class Worker(QtCore.QObject):
    finished = QtCore.Signal(object)
    error = QtCore.Signal(str)
    progress = QtCore.Signal(str)
    def __init__(self, fn):
        super().__init__(); self.fn = fn
    @QtCore.Slot()
    def run(self):
        try: self.finished.emit(self.fn(self.progress.emit))
        except Exception as exc: self.error.emit(f"{type(exc).__name__}: {exc}")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(APP_NAME); self.resize(900, 650)
        self.library = None; self._thread = None; self._worker = None; self.selected_files = []; self.generated = None
        self._build_ui(); self._load_library()

    def _build_ui(self):
        root = QtWidgets.QWidget(); layout = QtWidgets.QVBoxLayout(root)
        title = QtWidgets.QLabel(APP_NAME); title.setStyleSheet("font-size: 24px; font-weight: 700;"); layout.addWidget(title)
        self.drop = QtWidgets.QPushButton("Drop Acapella / Choose Vocal Files"); self.drop.setMinimumHeight(70); self.drop.clicked.connect(self.choose_files); layout.addWidget(self.drop)
        self.files_label = QtWidgets.QLabel("No vocal library loaded"); layout.addWidget(self.files_label)
        row = QtWidgets.QHBoxLayout(); self.analyze_btn = QtWidgets.QPushButton("Analyze Vocals"); self.analyze_btn.clicked.connect(self.analyze); row.addWidget(self.analyze_btn)
        self.status = QtWidgets.QLabel("Ready"); row.addWidget(self.status, 1); layout.addLayout(row)
        layout.addWidget(QtWidgets.QLabel("What should they say?")); self.text = QtWidgets.QPlainTextEdit(); self.text.setPlaceholderText("Type a sentence or lyric here..."); self.text.setMaximumHeight(130); layout.addWidget(self.text)
        controls = QtWidgets.QHBoxLayout(); controls.addWidget(QtWidgets.QLabel("Speed")); self.speed = QtWidgets.QDoubleSpinBox(); self.speed.setRange(0.5, 1.8); self.speed.setSingleStep(0.05); self.speed.setValue(1.0); controls.addWidget(self.speed)
        controls.addWidget(QtWidgets.QLabel("Crossfade (ms)")); self.crossfade = QtWidgets.QDoubleSpinBox(); self.crossfade.setRange(0, 50); self.crossfade.setValue(8); controls.addWidget(self.crossfade); controls.addStretch()
        self.generate_btn = QtWidgets.QPushButton("GENERATE"); self.generate_btn.setMinimumHeight(45); self.generate_btn.clicked.connect(self.generate_audio); controls.addWidget(self.generate_btn); layout.addLayout(controls)
        self.output_label = QtWidgets.QLabel("No generated audio yet"); layout.addWidget(self.output_label)
        self.export_btn = QtWidgets.QPushButton("Export WAV"); self.export_btn.clicked.connect(self.export_audio); self.export_btn.setEnabled(False); layout.addWidget(self.export_btn)
        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True); layout.addWidget(self.log, 1)
        self.setCentralWidget(root)

    def choose_files(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Choose Acapella", "", "Audio (*.wav *.flac *.ogg *.mp3 *.m4a)")
        if files: self.selected_files = files; self.files_label.setText(f"{len(files)} vocal file(s) selected")

    def _load_library(self):
        if LIB_PATH.exists():
            try: self.library = Library.load(LIB_PATH); self.files_label.setText(f"Loaded library: {len(self.library.segments)} segments")
            except Exception: self.library = None

    def _run_worker(self, fn, on_done):
        self._thread = QtCore.QThread(self); self._worker = Worker(fn); self._worker.moveToThread(self._thread); self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._set_status); self._worker.finished.connect(on_done); self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit); self._worker.error.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater); self._worker.error.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater); self._thread.finished.connect(self._worker_finished); self._thread.start()

    def _worker_finished(self): self._thread = None; self._worker = None
    def _set_status(self, msg): self.status.setText(msg); self.log.appendPlainText(msg)
    def _on_error(self, msg):
        self.status.setText("Error"); self.log.appendPlainText(msg); QtWidgets.QMessageBox.critical(self, APP_NAME, msg); self.analyze_btn.setEnabled(True); self.generate_btn.setEnabled(True)

    def analyze(self):
        if not self.selected_files: self.choose_files()
        if not self.selected_files: return
        self.analyze_btn.setEnabled(False); self.generate_btn.setEnabled(False)
        self._run_worker(lambda progress: analyze_files(self.selected_files, "tiny.en", progress), self._analysis_done)

    def _analysis_done(self, library):
        APP_DIR.mkdir(parents=True, exist_ok=True); library.save(LIB_PATH); self.library = library
        self.files_label.setText(f"Library ready: {len(library.segments)} segments"); self.status.setText("Analysis complete")
        self.analyze_btn.setEnabled(True); self.generate_btn.setEnabled(True)

    def generate_audio(self):
        if self.library is None: QtWidgets.QMessageBox.warning(self, APP_NAME, "Analyze an acapella first."); return
        text = self.text.toPlainText().strip()
        if not text: return
        self.generate_btn.setEnabled(False); speed = float(self.speed.value()); crossfade = float(self.crossfade.value())
        self._run_worker(lambda progress: generate(self.library, text, speed, crossfade, progress), self._generation_done)

    def _generation_done(self, result):
        self.generated = result; self.output_label.setText(f"Generated audio: {len(result[0]) / result[1]:.2f}s"); self.export_btn.setEnabled(True); self.generate_btn.setEnabled(True); self.status.setText("Generation complete")

    def export_audio(self):
        if self.generated is None: return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Vocal", "generated.wav", "WAV (*.wav)")
        if path: write_wav(path, *self.generated); self.output_label.setText(f"Saved: {path}")

    def closeEvent(self, event):
        if self._thread is not None and self._thread.isRunning(): self._thread.quit(); self._thread.wait(3000)
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv); app.setApplicationName(APP_NAME); window = MainWindow(); window.show(); sys.exit(app.exec())

if __name__ == "__main__": main()
