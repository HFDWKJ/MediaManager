"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.database import (
    Database, ExtractionRow, FOLDER_TYPE_COLLECTION, FOLDER_TYPE_ROOT,
    FOLDER_TYPE_LABELS,
)
from core.db_transfer import CatalogTransferError, default_export_filename
from core.device_manager import check_path_accessible, detect_device_type, device_identifier
from core.extraction_import import apply_folder_previews, preview_single_folder
from core.folder_refresh import refresh_folder_status
from core.file_ops import show_in_explorer
from core.names import format_display_name
from gui.about_dialog import AboutDialog
from gui.approve_dialog import ApproveFoldersDialog
from gui.database_table_panel import DatabaseTablePanel
from gui.detail_panel import DetailPanel
from gui.filter_bar import TreeFilterBar
from gui.library_tree_panel import LibraryTreePanel
from gui.face_uid_dialog import FaceUidDialog
from gui.name_match_dialog import NameMatchDialog
from gui.dg_theme import (
    THEME_DARK,
    THEME_LABELS,
    THEME_LIGHT,
    apply_theme,
    menu_bar_stylesheet,
    normalize_theme,
)
from gui.reorganize_dialog import ReorganizeDialog
from gui.settings_dialog import SettingsDialog
from gui.storage_map_bar import StorageMapBar
from core.device_types import DEVICE_TYPE_LABELS, normalize_device_type
from gui.workers import DiscoverWorker
from utils.config import AppConfig, LibraryRootConfig, load_config, save_config
from utils.paths import data_dir, is_portable_mode


class MainWindow(QMainWindow):
    def __init__(self, db: Database, app_config: AppConfig) -> None:
        super().__init__()
        self.db = db
        self.app_config = app_config
        self.setWindowTitle("Media Manager")
        self.resize(1280, 720)

        self._discover_worker: DiscoverWorker | None = None
        self._pending_root_id: int | None = None
        self._filter_root_id: int | None = None
        self._online_only = False
        self._extraction_count = 0
        self._filter_category: str | None = None
        self._current_theme = normalize_theme(
            app_config.get("ui", "theme", default=THEME_DARK)
        )

        self.library_panel = LibraryTreePanel(db)
        self.library_panel.root_selected.connect(self._on_root_selected)
        self.library_panel.all_roots_selected.connect(self._on_all_roots_selected)
        self.library_panel.add_to_database.connect(self._add_folder_from_library)
        self.library_panel.open_in_explorer.connect(self._show_path_in_explorer)
        self.library_panel.delete_library_root.connect(self._delete_library_root)
        self.library_panel.device_type_changed.connect(self.reload_extractions)
        self.library_panel.discover_on_root.connect(self._start_discover)
        self.library_panel.refresh_requested.connect(self._refresh_status)
        self.library_panel.category_selected.connect(self._on_category_selected)

        db_center = QWidget()
        db_center.setObjectName("dgCenterPanel")
        db_layout = QVBoxLayout(db_center)
        db_layout.setContentsMargins(0, 0, 0, 0)
        db_layout.setSpacing(0)
        self.storage_map = StorageMapBar()
        db_layout.addWidget(self.storage_map)
        self.filter_bar = TreeFilterBar()
        self.filter_bar.online_only_changed.connect(self._on_online_filter)
        db_layout.addWidget(self.filter_bar)
        self.database_panel = DatabaseTablePanel(db)
        self.database_panel.extraction_selected.connect(self._on_db_row_selected)
        self.database_panel.open_in_explorer.connect(self._show_extraction_in_explorer)
        db_layout.addWidget(self.database_panel, 1)

        self.detail = DetailPanel(db)
        self.detail.saved.connect(self._on_detail_saved)
        self.detail.delete_requested.connect(self._delete_extraction)
        self.database_panel.delete_requested.connect(self._delete_extraction)

        content_splitter = QSplitter()
        content_splitter.addWidget(self.library_panel)
        content_splitter.addWidget(db_center)
        content_splitter.addWidget(self.detail)
        content_splitter.setSizes([300, 520, 280])
        content_splitter.setCollapsible(0, False)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setStretchFactor(2, 0)

        shell = QWidget()
        shell.setObjectName("centralShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # Menu bar inside central layout — avoids QMainWindow menubar being
        # covered by the global stylesheet / central widget on Windows.
        self._menu_bar = QMenuBar(shell)
        self._menu_bar.setObjectName("appMenuBar")
        self._menu_bar.setNativeMenuBar(False)
        shell_layout.addWidget(self._menu_bar)
        shell_layout.addWidget(content_splitter, 1)
        self.setCentralWidget(shell)

        default_mb = self.menuBar()
        default_mb.clear()
        default_mb.setVisible(False)

        self._build_menu_bar(self._menu_bar)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        status = QStatusBar()
        status.addPermanentWidget(self.progress)
        self.setStatusBar(status)

        self._apply_dg_theme()
        self.db.ensure_config_roots(self.app_config.library_roots)
        self.library_panel.refresh(rebuild=True)
        self.library_panel.select_all_roots()
        self._filter_root_id = None
        self.reload_extractions()
        self._update_status()

    def _apply_dg_theme(self, theme: str | None = None) -> None:
        if theme is not None:
            self._current_theme = normalize_theme(theme)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, self._current_theme)
        self._menu_bar.setStyleSheet(menu_bar_stylesheet(self._current_theme))
        self.storage_map.set_theme(self._current_theme)
        self.library_panel.apply_theme(self._current_theme)
        QTimer.singleShot(0, self.library_panel._expand_default)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.app_config, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._set_theme(dlg.selected_theme(), persist=True)

    def _open_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    def _set_theme(self, theme: str, *, persist: bool) -> None:
        theme = normalize_theme(theme)
        if persist:
            if "ui" not in self.app_config.raw or not isinstance(self.app_config.raw["ui"], dict):
                self.app_config.raw["ui"] = {}
            self.app_config.raw["ui"]["theme"] = theme
            save_config(self.app_config)
        self._apply_dg_theme(theme)
        self._sync_theme_menu_checks()

    def _sync_theme_menu_checks(self) -> None:
        if not hasattr(self, "_theme_dark_action"):
            return
        self._theme_dark_action.blockSignals(True)
        self._theme_light_action.blockSignals(True)
        self._theme_dark_action.setChecked(self._current_theme == THEME_DARK)
        self._theme_light_action.setChecked(self._current_theme == THEME_LIGHT)
        self._theme_dark_action.blockSignals(False)
        self._theme_light_action.blockSignals(False)

    def reload_extractions(self) -> None:
        keep_id = self.detail.current_extraction_id()
        rows = self.db.get_extractions(online_only=self._online_only, root_id=self._filter_root_id)
        if self._filter_category:
            root_ids = {
                int(root["id"])
                for root in self.db.get_roots()
                if normalize_device_type(root["device_type"]) == self._filter_category
            }
            rows = [r for r in rows if r.root_id in root_ids]
        self._extraction_count = len(rows)
        self.database_panel.load_rows(rows)
        self.library_panel.refresh(self._filter_root_id)

        if keep_id is not None:
            self.database_panel.select_extraction_id(keep_id)
        elif rows:
            self.database_panel.table.selectRow(0)
            self._on_db_row_selected(rows[0])
        else:
            self.detail.set_extraction(None)

        filter_note = ""
        if self._filter_root_id is not None:
            filter_note = " · one library root"
        online_note = " · online only" if self._online_only else ""
        self.filter_bar.set_summary(
            f"{len(rows)} catalog row(s){filter_note}{online_note}"
        )
        self._update_storage_map()
        self._update_status()

    def _update_status(self) -> None:
        pending = len(self.db.get_pending_name_match_groups())
        total = self._extraction_count
        roots = len(self.db.get_roots())
        self.statusBar().showMessage(
            f"{roots} library root(s) | {total} catalog folders | {pending} pending matches"
        )

    def _on_root_selected(self, root_id: int) -> None:
        self._filter_root_id = root_id
        self.reload_extractions()

    def _on_all_roots_selected(self) -> None:
        self._filter_root_id = None
        self._filter_category = None
        self.reload_extractions()

    def _on_category_selected(self, device_type: str) -> None:
        self._filter_category = device_type
        self._filter_root_id = None
        self.reload_extractions()

    def _update_storage_map(self) -> None:
        roots = self.db.get_roots()
        title = "Storage map — all devices"
        segments: list[dict] = []
        for row in roots:
            dtype = normalize_device_type(row["device_type"])
            if self._filter_category and dtype != self._filter_category:
                continue
            if self._filter_root_id is not None and int(row["id"]) != self._filter_root_id:
                continue
            label = row["label"] or Path(row["root_path"]).name
            size = 1
            for ext in self.db.get_extractions(root_id=int(row["id"])):
                size += ext.total_size
            segments.append(
                {
                    "label": label,
                    "size": size,
                    "selected": self._filter_root_id == int(row["id"]),
                }
            )
        if self._filter_category:
            title = f"Storage map — {DEVICE_TYPE_LABELS.get(self._filter_category, self._filter_category)}"
        elif self._filter_root_id is not None:
            title = "Storage map — selected library root"
        self.storage_map.set_segments(title, segments)

    def _on_online_filter(self, enabled: bool) -> None:
        self._online_only = enabled
        online_action = getattr(self, "_online_action", None)
        if online_action is not None and online_action.isChecked() != enabled:
            online_action.blockSignals(True)
            online_action.setChecked(enabled)
            online_action.blockSignals(False)
        self.filter_bar.online_btn.blockSignals(True)
        self.filter_bar.online_btn.setChecked(enabled)
        self.filter_bar.online_btn.setText(f"Online only: {'On' if enabled else 'Off'}")
        self.filter_bar.online_btn.blockSignals(False)
        self.reload_extractions()

    def _on_db_row_selected(self, row: ExtractionRow | None) -> None:
        self.detail.set_extraction(row)

    def _on_detail_saved(self, extraction_id: int) -> None:
        self.reload_extractions()
        self._select_extraction_by_id(extraction_id)
        self.statusBar().showMessage("Catalog record updated", 4000)

    def _delete_library_root(self, root_id: int) -> None:
        root_path = ""
        root_label = ""
        for root in self.db.get_roots():
            if int(root["id"]) == root_id:
                root_path = str(root["root_path"])
                root_label = root["label"] or root_path
                break
        reply = QMessageBox.warning(
            self,
            "Delete library root",
            f"Remove library root <b>{root_label}</b> from the catalog?\n\n"
            f"Path: {root_path}\n\n"
            "All folders and files indexed under this root will be removed from the database.\n"
            "Files on disk are not deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_library_root(root_id)
        resolved = str(Path(root_path).resolve()) if root_path else ""
        if resolved:
            self.app_config.library_roots = [
                r for r in self.app_config.library_roots if r.path != resolved
            ]
            save_config(self.app_config)
        self._filter_root_id = None
        self.reload_extractions()
        self.library_panel.refresh(rebuild=True)
        self.library_panel.select_all_roots()
        self.statusBar().showMessage(f"Removed library root: {root_label}", 4000)

    def _delete_extraction(self, extraction_id: int) -> None:
        row = self.db.get_extraction_by_id(extraction_id)
        name = format_display_name(row.original_name) if row else f"#{extraction_id}"
        reply = QMessageBox.warning(
            self,
            "Delete record",
            f"Remove <b>{name}</b> from the database?\n\n"
            "Indexed files for this folder are removed from the catalog.\n"
            "Files on disk are not deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_extraction(extraction_id)
        self.reload_extractions()
        self.detail.set_extraction(None)
        self.statusBar().showMessage(f"Deleted catalog record: {name}", 4000)

    def _build_menu_bar(self, menu: QMenuBar) -> None:
        menu.setVisible(True)
        menu.setEnabled(True)

        file_menu = menu.addMenu("File")
        file_menu.addAction(self._action("Add library root…", self._add_root))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Clear database…", self._clear_database))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Exit", self.close))

        disk_menu = menu.addMenu("Disk")
        disk_menu.addAction(self._action("Refresh status", self._refresh_status, "F5"))
        disk_menu.addAction(self._action("Discover all roots", lambda: self._start_discover(None)))
        disk_menu.addAction(self._action("Discover selected root", self._discover_selected_root))

        catalog_menu = menu.addMenu("Catalog")
        catalog_menu.addAction(self._action("Select folder…", self._select_extraction_folder))
        catalog_menu.addAction(self._action("Mark as Root", lambda: self._set_folder_type(FOLDER_TYPE_ROOT)))
        catalog_menu.addAction(
            self._action("Mark as Collections", lambda: self._set_folder_type(FOLDER_TYPE_COLLECTION))
        )
        catalog_menu.addAction(self._action("Reorganize…", self._open_reorganize))

        tools_menu = menu.addMenu("Tools")
        tools_menu.addAction(self._action("Name matches…", self._open_matches))
        tools_menu.addAction(self._action("Face UID manager…", self._open_face_uid))
        tools_menu.addSeparator()
        tools_menu.addAction(self._action("Export database…", self._export_database))
        tools_menu.addAction(self._action("Import database…", self._import_database))
        tools_menu.addSeparator()
        tools_menu.addAction(self._action("Show in Explorer", self._show_explorer))
        options_menu = menu.addMenu("Options")
        options_menu.addAction(self._action("Settings…", self._open_settings))
        options_theme = options_menu.addMenu("Theme")
        self._theme_dark_action = QAction(THEME_LABELS[THEME_DARK], self)
        self._theme_dark_action.setCheckable(True)
        self._theme_dark_action.triggered.connect(
            lambda: self._set_theme(THEME_DARK, persist=True)
        )
        options_theme.addAction(self._theme_dark_action)
        self._theme_light_action = QAction(THEME_LABELS[THEME_LIGHT], self)
        self._theme_light_action.setCheckable(True)
        self._theme_light_action.triggered.connect(
            lambda: self._set_theme(THEME_LIGHT, persist=True)
        )
        options_theme.addAction(self._theme_light_action)
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        theme_group.addAction(self._theme_dark_action)
        theme_group.addAction(self._theme_light_action)

        options_menu.addSeparator()
        options_menu.addAction(self._action("About…", self._open_about))

        view_menu = menu.addMenu("View")
        self._online_action = QAction("Online only", self)
        self._online_action.setCheckable(True)
        self._online_action.triggered.connect(lambda c: self._on_online_filter(bool(c)))
        view_menu.addAction(self._online_action)

        self._sync_theme_menu_checks()

    def _action(self, text: str, slot, shortcut: str = "") -> QAction:
        act = QAction(text, self)
        act.triggered.connect(lambda _checked=False: slot())
        if shortcut:
            act.setShortcut(shortcut)
            act.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        return act

    def _selected_extraction(self) -> ExtractionRow | None:
        items = self.database_panel.table.selectedItems()
        if not items:
            return None
        return self.database_panel._row_at(items[0].row())

    def _select_extraction_by_id(self, extraction_id: int) -> None:
        self.database_panel.select_extraction_id(extraction_id)

    def _add_folder_from_library(self, folder: Path, root_id: int) -> None:
        if not check_path_accessible(folder):
            QMessageBox.warning(self, "Add to database", "Folder is not accessible.")
            return
        root_path = None
        for root in self.db.get_roots():
            if int(root["id"]) == root_id:
                root_path = Path(root["root_path"]).resolve()
                break
        if root_path:
            rel = str(folder.resolve().relative_to(root_path)).replace("\\", "/")
            if rel in self.db.get_extraction_paths_for_root(root_id):
                QMessageBox.information(
                    self,
                    "Add to database",
                    "This folder is already in the catalog.",
                )
                return
        try:
            preview = preview_single_folder(
                self.db, folder, self.app_config.raw, root_id=root_id
            )
        except (ValueError, FileNotFoundError) as e:
            QMessageBox.warning(self, "Add to database", str(e))
            return
        self._show_approve_dialog([preview], "Add to database")

    def _default_folder_dialog_path(self) -> str:
        if self._filter_root_id is not None:
            for root in self.db.get_roots():
                if int(root["id"]) == self._filter_root_id:
                    return str(root["root_path"])
        roots = self.db.get_roots()
        if roots:
            return str(roots[0]["root_path"])
        return str(Path.home())

    def _resolve_root_id_for_folder(self, folder: Path) -> int | None:
        if self._filter_root_id is None:
            return None
        for root in self.db.get_roots():
            if int(root["id"]) != self._filter_root_id:
                continue
            root_path = Path(root["root_path"]).resolve()
            try:
                folder.resolve().relative_to(root_path)
                return self._filter_root_id
            except ValueError:
                break
        return None

    def _select_extraction_folder(self) -> None:
        if not self.db.get_roots():
            QMessageBox.information(self, "Select Folder", "Add a library root first.")
            return
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Extraction Folder",
            self._default_folder_dialog_path(),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        if not path:
            return
        folder = Path(path)
        if not check_path_accessible(folder):
            QMessageBox.warning(self, "Select Folder", "Folder is not accessible.")
            return
        root_id = self._resolve_root_id_for_folder(folder)
        try:
            preview = preview_single_folder(
                self.db, folder, self.app_config.raw, root_id=root_id
            )
        except (ValueError, FileNotFoundError) as e:
            QMessageBox.warning(self, "Select Folder", str(e))
            return
        self._show_approve_dialog([preview], "Approve extraction folder")

    def _show_approve_dialog(self, previews: list, title: str) -> None:
        if not previews:
            QMessageBox.information(self, "Discover", "No folders found to add.")
            return
        dlg = ApproveFoldersDialog(previews, title, self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.approved:
            return
        ids = apply_folder_previews(self.db, dlg.approved, self.app_config.raw)
        self.reload_extractions()
        if ids:
            self._select_extraction_by_id(ids[0])
        QMessageBox.information(self, "Approved", f"Added {len(ids)} folder(s) to the catalog.")

    def _add_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Library Root Folder")
        if not path:
            return
        p = Path(path)
        if not check_path_accessible(p):
            QMessageBox.warning(self, "Path", "Folder is not accessible.")
            return
        ident = device_identifier(p)
        device = self.db.get_device_by_identifier(ident)
        if device:
            device_id = int(device["id"])
        else:
            device_id = self.db.insert_device(
                name=p.drive or p.name,
                device_type=detect_device_type(p),
                identifier=ident,
                mount_hint=str(p),
            )
        self.db.insert_root(device_id, str(p.resolve()), p.name)
        resolved = str(p.resolve())
        if not any(r.path == resolved for r in self.app_config.library_roots):
            self.app_config.library_roots.append(
                LibraryRootConfig(
                    device_name=p.drive or "Local",
                    device_type=detect_device_type(p),
                    path=resolved,
                    label=p.name,
                )
            )
            save_config(self.app_config)
        self._filter_root_id = None
        self.library_panel.refresh(rebuild=True)
        self.library_panel.select_all_roots()
        self.reload_extractions()
        QMessageBox.information(
            self,
            "Added",
            f"Library root added:\n{p}\n\n"
            "Browse folders in the Library tree and right-click <b>Add to database</b>.",
        )

    def _discover_selected_root(self) -> None:
        if self._filter_root_id is None:
            QMessageBox.information(self, "Discover", "Select a library root in the Library panel first.")
            return
        self._start_discover(self._filter_root_id)

    def _start_discover(self, root_id: int | None) -> None:
        if self._discover_worker and self._discover_worker.isRunning():
            QMessageBox.information(self, "Discover", "Discovery already in progress.")
            return
        self._pending_root_id = root_id
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.statusBar().showMessage("Discovering folders on disk…")
        self._discover_worker = DiscoverWorker(self.db, self.app_config.raw, root_id)
        self._discover_worker.finished_ok.connect(self._on_discover_done)
        self._discover_worker.error.connect(self._on_discover_error)
        self._discover_worker.start()

    def _on_discover_done(self, previews: list) -> None:
        self.progress.setVisible(False)
        title = "Approve discovered folders"
        if self._pending_root_id is not None:
            title = "Approve folders on selected library root"
        self._show_approve_dialog(previews, title)

    def _on_discover_error(self, msg: str) -> None:
        self.progress.setVisible(False)
        QMessageBox.warning(self, "Discover Error", msg)

    def _refresh_status(self) -> None:
        result = refresh_folder_status(
            self.db, self.app_config.raw, root_id=self._filter_root_id
        )
        self.reload_extractions()
        QMessageBox.information(
            self,
            "Refresh Complete",
            f"Updated: {result.updated}\nOffline: {result.offline}\nMissing: {result.missing}",
        )

    def _clear_database(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Clear Database",
            "Delete ALL catalog data?\n\nLibrary paths in config are kept.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.db.clear_all_catalog_data()
        self.reload_extractions()
        self.detail.set_extraction(None)
        QMessageBox.information(self, "Cleared", "Database cleared.")

    def _open_matches(self) -> None:
        dlg = NameMatchDialog(self.db, self)
        dlg.exec()
        self.reload_extractions()

    def _open_face_uid(self) -> None:
        dlg = FaceUidDialog(self.db, self)
        dlg.exec()

    def _export_database(self) -> None:
        if self._discover_worker and self._discover_worker.isRunning():
            QMessageBox.information(
                self,
                "Export database",
                "Wait for discovery to finish before exporting.",
            )
            return
        default_name = default_export_filename()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export database",
            str(Path.home() / default_name),
            "SQLite catalog (*.db);;All files (*.*)",
        )
        if not path:
            return
        export_path = Path(path)
        if export_path.suffix.lower() != ".db":
            export_path = export_path.with_suffix(".db")
        try:
            self.db.export_to(export_path)
        except CatalogTransferError as e:
            QMessageBox.warning(self, "Export database", str(e))
            return
        except OSError as e:
            QMessageBox.warning(self, "Export database", f"Could not write file:\n{e}")
            return
        QMessageBox.information(
            self,
            "Export database",
            f"Catalog exported successfully.\n\n{export_path.resolve()}",
        )

    def _import_database(self) -> None:
        if self._discover_worker and self._discover_worker.isRunning():
            QMessageBox.information(
                self,
                "Import database",
                "Wait for discovery to finish before importing.",
            )
            return
        if is_portable_mode():
            data_note = (
                f"Catalog data is stored in:\n{data_dir()}\n\n"
                "Copy the whole application folder to another PC to keep settings "
                "and the database together.\n\n"
            )
        else:
            data_note = (
                "Catalog data is stored under %APPDATA%\\MediaManager\\.\n\n"
            )
        reply = QMessageBox.warning(
            self,
            "Import database",
            data_note
            + "Replace the current catalog with a backup file?\n\n"
            "Library folder paths in Settings are not changed — adjust them "
            "on each device if drive letters differ.\n\n"
            "Export a backup first if you are unsure.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import database",
            str(Path.home()),
            "SQLite catalog (*.db);;All files (*.*)",
        )
        if not path:
            return
        import_path = Path(path)
        try:
            self.db.import_from(import_path)
        except CatalogTransferError as e:
            QMessageBox.warning(self, "Import database", str(e))
            return
        except OSError as e:
            QMessageBox.warning(self, "Import database", f"Could not read file:\n{e}")
            return
        self._reload_catalog_ui()
        QMessageBox.information(
            self,
            "Import database",
            "Catalog imported successfully.\n\n"
            "Review library roots and folder availability on this device.",
        )

    def _reload_catalog_ui(self) -> None:
        self.db.ensure_config_roots(self.app_config.library_roots)
        self._filter_root_id = None
        self.library_panel.refresh(rebuild=True)
        self.library_panel.select_all_roots()
        self.reload_extractions()
        self.detail.set_extraction(None)

    def _set_folder_type(self, folder_type: str) -> None:
        row = self._selected_extraction()
        if not row:
            QMessageBox.information(self, "Folder type", "Select a row in the Database table first.")
            return
        self.db.set_folder_type(row.id, folder_type)
        self.reload_extractions()
        label = FOLDER_TYPE_LABELS.get(folder_type, folder_type)
        self.statusBar().showMessage(f"Marked as {label}: {format_display_name(row.original_name)}")

    def _open_reorganize(self) -> None:
        row = self._selected_extraction()
        if not row:
            QMessageBox.information(self, "Reorganize", "Select a folder in the Database table first.")
            return
        if row.folder_type != FOLDER_TYPE_COLLECTION:
            QMessageBox.warning(
                self,
                "Reorganize",
                "Reorganize only works on Collections folders.\n"
                "Mark the folder as Collections first.",
            )
            return
        if row.availability != "online":
            QMessageBox.warning(self, "Reorganize", "Folder is offline.")
            return
        dlg = ReorganizeDialog(self.db, row.id, self.app_config.raw, self)
        dlg.exec()

    def _show_explorer(self) -> None:
        row = self._selected_extraction()
        if row:
            self._show_extraction_in_explorer(row)

    def _show_extraction_in_explorer(self, row: ExtractionRow) -> None:
        path = Path(row.root_path) / row.folder_path
        if not show_in_explorer(path):
            QMessageBox.warning(self, "Explorer", f"Cannot open:\n{path}")

    def _show_path_in_explorer(self, path: Path) -> None:
        if not show_in_explorer(path):
            QMessageBox.warning(self, "Explorer", f"Cannot open:\n{path}")
