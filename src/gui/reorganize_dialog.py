"""Preview and execute reorganize (flatten + rename)."""

from __future__ import annotations

import time

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from core.database import Database, FOLDER_TYPE_COLLECTION
from core.name_matcher import suggest_new_folder_name
from core.reorganize import build_reorganize_plan
from gui.workers import ReorganizeWorker


class ReorganizeDialog(QDialog):
    def __init__(self, db: Database, extraction_id: int, config: dict, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self.extraction_id = extraction_id
        self.config = config
        self.plan = None
        self._run_started_at: float | None = None
        self.setWindowTitle("Reorganize — New Folder Name")
        self.resize(800, 500)
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("New Folder Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(suggest_new_folder_name(db, extraction_id))
        row.addWidget(self.name_input)
        self.preview_btn = QPushButton("Preview")
        row.addWidget(self.preview_btn)
        layout.addLayout(row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Seq", "Original Path", "Original File", "New Filename"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.progress_label = QLabel("Ready")
        self.progress_label.setObjectName("dgPanelHint")
        layout.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Confirm & Reorganize")
        self.run_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.preview_btn.clicked.connect(self._preview)
        self.run_btn.clicked.connect(self._run)
        self.cancel_btn.clicked.connect(self.reject)

    def _preview(self) -> None:
        row = self.db.get_extraction(self.extraction_id)
        if row and row["folder_type"] != FOLDER_TYPE_COLLECTION:
            QMessageBox.warning(
                self,
                "Reorganize",
                "Only [Collections] folders can be reorganized.",
            )
            return
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input", "Enter a New Folder Name.")
            return
        self.plan = build_reorganize_plan(self.db, self.extraction_id, name, self.config)
        if not self.plan:
            QMessageBox.warning(
                self,
                "Error",
                "Could not build plan. Folder must be [Collections], online, and accessible.",
            )
            return
        self.table.setRowCount(len(self.plan.rows))
        for i, row in enumerate(self.plan.rows):
            self.table.setItem(i, 0, QTableWidgetItem(f"{row.sequence:04d}"))
            self.table.setItem(i, 1, QTableWidgetItem(row.original_relative))
            self.table.setItem(i, 2, QTableWidgetItem(row.original_filename))
            self.table.setItem(i, 3, QTableWidgetItem(row.new_filename))
        self.run_btn.setEnabled(True)

    def _run(self) -> None:
        if not self.plan:
            return
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Flatten and rename {len(self.plan.rows)} files into folder \"{self.plan.new_folder_name}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.run_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.name_input.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.plan.rows) if self.plan.rows else 1)
        self.progress.setValue(0)
        self._run_started_at = time.monotonic()
        self.progress_label.setText("Reorganize started… (0.0% • ETA --:--)")
        self._worker = ReorganizeWorker(self.db, self.plan, self.config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, cur: int, total: int, name: str) -> None:
        total = max(1, total)
        cur = min(cur, total)
        self.progress.setRange(0, total)
        self.progress.setValue(cur)
        percent = (cur / total) * 100.0
        eta_text = self._eta_text(cur, total)
        self.progress_label.setText(
            f"Processing {cur}/{total} ({percent:.1f}% • ETA {eta_text}): {name}"
        )

    def _on_done(self, ok: bool) -> None:
        if ok:
            self.progress.setValue(self.progress.maximum())
            self.progress_label.setText("Reorganize completed. (100.0% • ETA 00:00)")
            QMessageBox.information(
                self,
                "Done",
                "Reorganize completed.\n\n"
                "A timestamped CSV report was written in the folder\n"
                "(reorganize_YYYYMMDD_HHMMSS.csv).",
            )
            parent = self.parent()
            if parent is not None:
                if hasattr(parent, "reload_extractions"):
                    parent.reload_extractions()
                if hasattr(parent, "library_panel"):
                    parent.library_panel.refresh(rebuild=True)
            self.accept()
        else:
            QMessageBox.warning(self, "Failed", "Reorganize failed. Check logs.")
            self._reset_controls_after_run()

    def _on_error(self, msg: str) -> None:
        QMessageBox.warning(self, "Error", msg)
        self.progress_label.setText("Reorganize failed.")
        self._reset_controls_after_run()

    def _reset_controls_after_run(self) -> None:
        self.run_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.name_input.setEnabled(True)
        self._run_started_at = None

    def _eta_text(self, cur: int, total: int) -> str:
        if cur <= 0 or self._run_started_at is None:
            return "--:--"
        elapsed = max(0.0, time.monotonic() - self._run_started_at)
        avg_per_item = elapsed / cur
        remaining_sec = int(round(avg_per_item * max(0, total - cur)))
        minutes, seconds = divmod(remaining_sec, 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
