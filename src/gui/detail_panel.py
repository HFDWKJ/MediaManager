"""Detail panel: view and edit a single catalog record."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)

from core.database import (
    Database,
    ExtractionRow,
    FOLDER_TYPE_COLLECTION,
    FOLDER_TYPE_LABELS,
    FOLDER_TYPE_ROOT,
)
from core.name_matcher import normalize_name
from core.names import format_display_name


class DetailPanel(QWidget):
    saved = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self.setMinimumWidth(260)

        self.setObjectName("dgRightPanel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        heading = QLabel("Properties")
        heading.setObjectName("dgPanelTitle")
        outer.addWidget(heading)

        self.title = QLabel("Select a row in the Database table")
        self.title.setWordWrap(True)
        outer.addWidget(self.title)

        # Save / Delete always at top — not pushed off-screen
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save changes")
        self.save_btn.setObjectName("actionPrimary")
        self.save_btn.setMinimumHeight(36)
        self.save_btn.clicked.connect(self._save)
        self.delete_btn = QPushButton("Delete record")
        self.delete_btn.setObjectName("actionDanger")
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.clicked.connect(self._request_delete)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.delete_btn)
        outer.addLayout(btn_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_host = QWidget()
        form_layout = QVBoxLayout(form_host)
        form_layout.setContentsMargins(0, 0, 4, 0)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Relative path under library root")
        self.type_combo = QComboBox()
        self.type_combo.addItem(FOLDER_TYPE_LABELS[FOLDER_TYPE_ROOT], FOLDER_TYPE_ROOT)
        self.type_combo.addItem(FOLDER_TYPE_LABELS[FOLDER_TYPE_COLLECTION], FOLDER_TYPE_COLLECTION)
        self.availability_combo = QComboBox()
        for val in ("online", "offline", "missing"):
            self.availability_combo.addItem(val.capitalize(), val)
        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("Target name for reorganize (optional)")
        self.reorganize_combo = QComboBox()
        for val in ("pending", "completed", "skipped"):
            self.reorganize_combo.addItem(val.capitalize(), val)
        self.device_label = QLabel("—")
        self.library_label = QLabel("—")
        self.library_label.setWordWrap(True)
        self.match_label = QLabel("—")
        self.files_label = QLabel("—")
        self.pre_folder_label = QLabel("—")
        self.pre_folder_label.setWordWrap(True)

        form.addRow("Display name:", self.name_edit)
        form.addRow("Folder path:", self.path_edit)
        form.addRow("Folder type:", self.type_combo)
        form.addRow("Availability:", self.availability_combo)
        form.addRow("New folder name:", self.new_name_edit)
        form.addRow("Reorganize:", self.reorganize_combo)
        form.addRow("Device:", self.device_label)
        form.addRow("Library root:", self.library_label)
        form.addRow("Match:", self.match_label)
        form.addRow("Indexed:", self.files_label)
        form.addRow("Folder before reorganize:", self.pre_folder_label)
        form_layout.addLayout(form)

        self.reorganize_hint = QLabel()
        self.reorganize_hint.setWordWrap(True)
        form_layout.addWidget(self.reorganize_hint)

        form_layout.addWidget(QLabel("Notes:"))
        self.notes = QTextEdit()
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)
        form_layout.addWidget(self.notes)

        scroll.setWidget(form_host)
        outer.addWidget(scroll, 1)

        self._row: ExtractionRow | None = None
        self._set_editing_enabled(False)

    def _set_editing_enabled(self, enabled: bool) -> None:
        for w in (
            self.name_edit, self.path_edit, self.type_combo, self.availability_combo,
            self.new_name_edit, self.reorganize_combo, self.notes,
            self.save_btn, self.delete_btn,
        ):
            w.setEnabled(enabled)

    def set_extraction(self, row: ExtractionRow | None) -> None:
        self._row = row
        if not row:
            self.title.setText("Select a row in the Database table")
            self.device_label.setText("—")
            self.library_label.setText("—")
            self.match_label.setText("—")
            self.files_label.setText("—")
            self.pre_folder_label.setText("—")
            self.name_edit.clear()
            self.path_edit.clear()
            self.new_name_edit.clear()
            self.notes.clear()
            self._set_editing_enabled(False)
            return

        self.title.setText(f"<b>#{row.id}</b> — {format_display_name(row.original_name)}")
        self.name_edit.setText(format_display_name(row.original_name))
        self.path_edit.setText(row.folder_path.replace("\\", "/"))
        idx = self.type_combo.findData(row.folder_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        av_idx = self.availability_combo.findData(row.availability)
        if av_idx >= 0:
            self.availability_combo.setCurrentIndex(av_idx)
        self.new_name_edit.setText(row.new_folder_name or "")
        rs_idx = self.reorganize_combo.findData(row.reorganize_status)
        if rs_idx >= 0:
            self.reorganize_combo.setCurrentIndex(rs_idx)
        else:
            self.reorganize_combo.setCurrentIndex(0)

        self.device_label.setText(row.device_name)
        self.library_label.setText(f"{row.root_label}\n{row.root_path}")
        status_map = {
            "exact": "🟡 Exact name match",
            "similar": "🟠 Similar name match",
            "hash_confirmed": "🟢 Hash confirmed",
            "none": "No match",
        }
        self.match_label.setText(status_map.get(row.match_status, row.match_status))
        self.files_label.setText(f"{row.file_count} files, {row.total_size / 1024 / 1024:.1f} MB")
        if row.pre_reorganize_folder_path or row.pre_reorganize_folder_name:
            parts = []
            if row.pre_reorganize_folder_name:
                parts.append(row.pre_reorganize_folder_name)
            if row.pre_reorganize_folder_path:
                parts.append(row.pre_reorganize_folder_path)
            self.pre_folder_label.setText("\n".join(parts))
        else:
            self.pre_folder_label.setText("— (not reorganized yet)")
        self.notes.setPlainText(row.notes or "")
        self._update_reorganize_hint(str(self.type_combo.currentData()))
        self._set_editing_enabled(True)

    def _update_reorganize_hint(self, folder_type: str) -> None:
        if folder_type == FOLDER_TYPE_COLLECTION:
            self.reorganize_hint.setText(
                "<i>Collections — use Reorganize on the Ribbon (Folder tab).</i>"
            )
        else:
            self.reorganize_hint.setText(
                "<i>Root = structural. Set type to Collections for extracted content.</i>"
            )

    def _save(self) -> None:
        if not self._row:
            return
        name = self.name_edit.text().strip()
        folder_path = self.path_edit.text().strip().replace("\\", "/")
        if not name:
            QMessageBox.warning(self, "Save", "Display name cannot be empty.")
            return
        if not folder_path or folder_path == ".":
            QMessageBox.warning(self, "Save", "Folder path cannot be empty.")
            return

        new_folder = self.new_name_edit.text().strip() or None
        notes_text = self.notes.toPlainText().strip() or None
        folder_type = str(self.type_combo.currentData())
        availability = str(self.availability_combo.currentData())
        reorganize_status = str(self.reorganize_combo.currentData())

        try:
            self.db.update_extraction_catalog(
                self._row.id,
                original_name=name,
                normalized_name=normalize_name(name),
                folder_path=folder_path,
                folder_type=folder_type,
                new_folder_name=new_folder,
                availability=availability,
                reorganize_status=reorganize_status,
                notes=notes_text,
            )
        except Exception as e:
            QMessageBox.warning(self, "Save", f"Could not save:\n{e}")
            return

        self.saved.emit(self._row.id)

    def _request_delete(self) -> None:
        if self._row:
            self.delete_requested.emit(self._row.id)

    def current_extraction_id(self) -> int | None:
        return self._row.id if self._row else None

    def current_folder_type(self) -> str | None:
        return self._row.folder_type if self._row else None
