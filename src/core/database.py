"""SQLite catalog database."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterator

from core.db_transfer import (
    CatalogTransferError,
    export_catalog_database,
    import_catalog_database,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS StorageDevice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'unknown',
    identifier TEXT,
    mount_hint TEXT,
    is_online INTEGER NOT NULL DEFAULT 1,
    last_seen TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS LibraryRoot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL REFERENCES StorageDevice(id) ON DELETE CASCADE,
    root_path TEXT NOT NULL,
    label TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_scan TEXT,
    file_count INTEGER DEFAULT 0,
    UNIQUE(device_id, root_path)
);

CREATE TABLE IF NOT EXISTS ExtractionFolder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id INTEGER NOT NULL REFERENCES LibraryRoot(id) ON DELETE CASCADE,
    folder_path TEXT NOT NULL,
    original_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    file_count INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    date_indexed TEXT,
    availability TEXT NOT NULL DEFAULT 'online',
    folder_type TEXT NOT NULL DEFAULT 'collection',
    new_folder_name TEXT,
    reorganize_status TEXT DEFAULT 'pending',
    reorganized_at TEXT,
    UNIQUE(root_id, folder_path)
);

CREATE TABLE IF NOT EXISTS Media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id INTEGER NOT NULL REFERENCES LibraryRoot(id) ON DELETE CASCADE,
    extraction_id INTEGER REFERENCES ExtractionFolder(id) ON DELETE SET NULL,
    relative_path TEXT NOT NULL,
    absolute_path TEXT,
    folder_path TEXT,
    depth INTEGER DEFAULT 0,
    original_name TEXT,
    file_hash TEXT,
    file_size INTEGER,
    file_type TEXT,
    mime_type TEXT,
    mtime TEXT,
    availability TEXT NOT NULL DEFAULT 'online',
    status TEXT NOT NULL DEFAULT 'indexed',
    date_added TEXT,
    last_verified TEXT,
    UNIQUE(root_id, relative_path)
);

CREATE TABLE IF NOT EXISTS Metadata (
    media_id INTEGER PRIMARY KEY REFERENCES Media(id) ON DELETE CASCADE,
    source_url TEXT,
    source_site TEXT,
    source_id TEXT,
    original_filename TEXT,
    download_tool TEXT,
    download_date TEXT,
    description TEXT,
    tags TEXT,
    notes TEXT,
    custom_fields TEXT,
    original_details TEXT
);

CREATE TABLE IF NOT EXISTS DownloadHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER REFERENCES Media(id) ON DELETE SET NULL,
    extraction_id INTEGER REFERENCES ExtractionFolder(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    old_path TEXT,
    new_path TEXT,
    timestamp TEXT NOT NULL,
    details TEXT
);

CREATE TABLE IF NOT EXISTS Archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER REFERENCES Media(id) ON DELETE CASCADE,
    extraction_id INTEGER REFERENCES ExtractionFolder(id) ON DELETE SET NULL,
    has_password INTEGER DEFAULT 0,
    extracted_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS NameMatchGroup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_name TEXT NOT NULL,
    match_type TEXT NOT NULL,
    similarity_score REAL,
    member_count INTEGER DEFAULT 0,
    review_status TEXT NOT NULL DEFAULT 'pending',
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS NameMatchMember (
    group_id INTEGER NOT NULL REFERENCES NameMatchGroup(id) ON DELETE CASCADE,
    extraction_id INTEGER NOT NULL REFERENCES ExtractionFolder(id) ON DELETE CASCADE,
    is_primary INTEGER DEFAULT 0,
    PRIMARY KEY (group_id, extraction_id)
);

CREATE TABLE IF NOT EXISTS DuplicateGroup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash TEXT NOT NULL,
    file_size INTEGER,
    member_count INTEGER DEFAULT 0,
    source_name_group_id INTEGER REFERENCES NameMatchGroup(id),
    reviewed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS DuplicateMember (
    group_id INTEGER NOT NULL REFERENCES DuplicateGroup(id) ON DELETE CASCADE,
    media_id INTEGER REFERENCES Media(id) ON DELETE CASCADE,
    extraction_id INTEGER REFERENCES ExtractionFolder(id) ON DELETE CASCADE,
    is_primary INTEGER DEFAULT 0,
    PRIMARY KEY (group_id, media_id, extraction_id)
);

CREATE INDEX IF NOT EXISTS idx_media_hash ON Media(file_hash);
CREATE INDEX IF NOT EXISTS idx_media_size ON Media(file_size);
CREATE INDEX IF NOT EXISTS idx_media_root ON Media(root_id);
CREATE INDEX IF NOT EXISTS idx_extraction_norm ON ExtractionFolder(normalized_name);

CREATE TABLE IF NOT EXISTS Face_UID (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    nick_name TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    comments TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_face_uid_uid ON Face_UID(uid);
"""

# Folder classification for user workflow
FOLDER_TYPE_ROOT = "root"
FOLDER_TYPE_COLLECTION = "collection"

FOLDER_TYPE_LABELS = {
    FOLDER_TYPE_ROOT: "Root",
    FOLDER_TYPE_COLLECTION: "Collections",
}


@dataclass
class ExtractionRow:
    id: int
    root_id: int
    folder_path: str
    original_name: str
    normalized_name: str
    file_count: int
    total_size: int
    availability: str
    new_folder_name: str | None
    reorganize_status: str
    folder_type: str = FOLDER_TYPE_ROOT
    device_name: str = ""
    root_label: str = ""
    root_path: str = ""
    match_status: str = ""  # exact, similar, hash_confirmed, none
    match_group_id: int | None = None
    notes: str | None = None
    pre_reorganize_folder_path: str | None = None
    pre_reorganize_folder_name: str | None = None


@dataclass
class FaceUidRow:
    id: int
    uid: str
    nick_name: str
    region: str
    comments: str
    created_at: str


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate_schema(conn)

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(ExtractionFolder)")}
        if "folder_type" not in cols:
            conn.execute(
                """
                ALTER TABLE ExtractionFolder
                ADD COLUMN folder_type TEXT NOT NULL DEFAULT 'collection'
                """
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_extraction_type ON ExtractionFolder(folder_type)"
        )
        if "notes" not in cols:
            conn.execute("ALTER TABLE ExtractionFolder ADD COLUMN notes TEXT")
        if "pre_reorganize_folder_path" not in cols:
            conn.execute(
                "ALTER TABLE ExtractionFolder ADD COLUMN pre_reorganize_folder_path TEXT"
            )
        if "pre_reorganize_folder_name" not in cols:
            conn.execute(
                "ALTER TABLE ExtractionFolder ADD COLUMN pre_reorganize_folder_name TEXT"
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Face_UID (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL UNIQUE,
                nick_name TEXT NOT NULL DEFAULT '',
                region TEXT NOT NULL DEFAULT '',
                comments TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_face_uid_uid ON Face_UID(uid)"
        )

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- Devices ---
    def insert_device(
        self,
        name: str,
        device_type: str = "unknown",
        identifier: str | None = None,
        mount_hint: str | None = None,
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO StorageDevice (name, type, identifier, mount_hint, is_online, last_seen)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (name, device_type, identifier, mount_hint, _utc_now()),
            )
            return int(cur.lastrowid)

    def get_device_by_identifier(self, identifier: str) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM StorageDevice WHERE identifier = ?", (identifier,)
            ).fetchone()

    def get_devices(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute("SELECT * FROM StorageDevice ORDER BY name"))

    def update_device_online(self, device_id: int, is_online: bool) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE StorageDevice SET is_online = ?, last_seen = ? WHERE id = ?",
                (1 if is_online else 0, _utc_now(), device_id),
            )

    def update_device_type(self, device_id: int, device_type: str) -> None:
        from core.device_types import normalize_device_type

        device_type = normalize_device_type(device_type)
        with self.connect() as conn:
            conn.execute(
                "UPDATE StorageDevice SET type = ? WHERE id = ?",
                (device_type, device_id),
            )

    def delete_library_root(self, root_id: int) -> None:
        """Remove library root and catalog data under it (CASCADE)."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT device_id FROM LibraryRoot WHERE id = ?", (root_id,)
            ).fetchone()
            conn.execute("DELETE FROM LibraryRoot WHERE id = ?", (root_id,))
            if row:
                device_id = int(row["device_id"])
                remaining = conn.execute(
                    "SELECT COUNT(*) AS c FROM LibraryRoot WHERE device_id = ?",
                    (device_id,),
                ).fetchone()
                if remaining and int(remaining["c"]) == 0:
                    conn.execute("DELETE FROM StorageDevice WHERE id = ?", (device_id,))

    # --- Roots ---
    def insert_root(
        self, device_id: int, root_path: str, label: str = "", enabled: bool = True
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO LibraryRoot (device_id, root_path, label, enabled)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_id, root_path) DO UPDATE SET label=excluded.label
                """,
                (device_id, root_path, label, 1 if enabled else 0),
            )
            row = conn.execute(
                "SELECT id FROM LibraryRoot WHERE device_id = ? AND root_path = ?",
                (device_id, root_path),
            ).fetchone()
            return int(row["id"]) if row else int(cur.lastrowid)

    def get_roots(self, enabled_only: bool = False) -> list[sqlite3.Row]:
        sql = """
            SELECT r.*, d.name AS device_name, d.type AS device_type, d.is_online
            FROM LibraryRoot r
            JOIN StorageDevice d ON d.id = r.device_id
        """
        if enabled_only:
            sql += " WHERE r.enabled = 1"
        sql += " ORDER BY d.name, r.label"
        with self.connect() as conn:
            return list(conn.execute(sql))

    def update_root_scan(self, root_id: int, file_count: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE LibraryRoot SET last_scan = ?, file_count = ? WHERE id = ?",
                (_utc_now(), file_count, root_id),
            )

    # --- Extractions ---
    def upsert_extraction(
        self,
        root_id: int,
        folder_path: str,
        original_name: str,
        normalized_name: str,
        file_count: int,
        total_size: int,
        availability: str = "online",
        folder_type: str = FOLDER_TYPE_COLLECTION,
    ) -> int:
        now = _utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO ExtractionFolder (
                    root_id, folder_path, original_name, normalized_name,
                    file_count, total_size, date_indexed, availability, folder_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(root_id, folder_path) DO UPDATE SET
                    original_name=excluded.original_name,
                    normalized_name=excluded.normalized_name,
                    file_count=excluded.file_count,
                    total_size=excluded.total_size,
                    availability=excluded.availability
                """,
                (
                    root_id, folder_path, original_name, normalized_name,
                    file_count, total_size, now, availability, folder_type,
                ),
            )
            row = conn.execute(
                "SELECT id FROM ExtractionFolder WHERE root_id = ? AND folder_path = ?",
                (root_id, folder_path),
            ).fetchone()
            return int(row["id"])

    def set_folder_type(self, extraction_id: int, folder_type: str) -> None:
        if folder_type not in (FOLDER_TYPE_ROOT, FOLDER_TYPE_COLLECTION):
            folder_type = FOLDER_TYPE_COLLECTION
        with self.connect() as conn:
            conn.execute(
                "UPDATE ExtractionFolder SET folder_type = ? WHERE id = ?",
                (folder_type, extraction_id),
            )

    def get_extractions(
        self,
        online_only: bool = False,
        root_id: int | None = None,
        folder_type: str | None = None,
    ) -> list[ExtractionRow]:
        sql = """
            SELECT e.*, r.label AS root_label, r.root_path, d.name AS device_name
            FROM ExtractionFolder e
            JOIN LibraryRoot r ON r.id = e.root_id
            JOIN StorageDevice d ON d.id = r.device_id
            WHERE 1=1
        """
        params: list[Any] = []
        if online_only:
            sql += " AND e.availability = 'online' AND d.is_online = 1"
        if root_id is not None:
            sql += " AND e.root_id = ?"
            params.append(root_id)
        if folder_type is not None:
            sql += " AND e.folder_type = ?"
            params.append(folder_type)
        sql += " ORDER BY e.folder_type, e.original_name"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        result: list[ExtractionRow] = []
        for row in rows:
            match_status, group_id = self._extraction_match_info(int(row["id"]))
            result.append(
                ExtractionRow(
                    id=int(row["id"]),
                    root_id=int(row["root_id"]),
                    folder_path=row["folder_path"],
                    original_name=row["original_name"],
                    normalized_name=row["normalized_name"],
                    file_count=int(row["file_count"] or 0),
                    total_size=int(row["total_size"] or 0),
                    availability=row["availability"],
                    new_folder_name=row["new_folder_name"],
                    reorganize_status=row["reorganize_status"] or "pending",
                    folder_type=row["folder_type"] or FOLDER_TYPE_ROOT,
                    device_name=row["device_name"],
                    root_label=row["root_label"] or "",
                    root_path=row["root_path"],
                    match_status=match_status,
                    match_group_id=group_id,
                    notes=row["notes"] if "notes" in row.keys() else None,
                    pre_reorganize_folder_path=(
                        row["pre_reorganize_folder_path"]
                        if "pre_reorganize_folder_path" in row.keys()
                        else None
                    ),
                    pre_reorganize_folder_name=(
                        row["pre_reorganize_folder_name"]
                        if "pre_reorganize_folder_name" in row.keys()
                        else None
                    ),
                )
            )
        return result

    def get_extraction_by_id(self, extraction_id: int) -> ExtractionRow | None:
        for ext in self.get_extractions():
            if ext.id == extraction_id:
                return ext
        return None

    @staticmethod
    def folder_type_label(folder_type: str) -> str:
        return FOLDER_TYPE_LABELS.get(folder_type, FOLDER_TYPE_LABELS[FOLDER_TYPE_ROOT])

    def _extraction_match_info(self, extraction_id: int) -> tuple[str, int | None]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT g.id, g.match_type, g.review_status
                FROM NameMatchMember m
                JOIN NameMatchGroup g ON g.id = m.group_id
                WHERE m.extraction_id = ? AND g.review_status = 'pending'
                LIMIT 1
                """,
                (extraction_id,),
            ).fetchone()
            if row:
                return str(row["match_type"]), int(row["id"])
            row = conn.execute(
                """
                SELECT g.id FROM DuplicateMember dm
                JOIN DuplicateGroup g ON g.id = dm.group_id
                WHERE dm.extraction_id = ?
                LIMIT 1
                """,
                (extraction_id,),
            ).fetchone()
            if row:
                return "hash_confirmed", int(row["id"])
        return "none", None

    def get_extractions_by_normalized_name(
        self, normalized_name: str, exclude_id: int | None = None
    ) -> list[sqlite3.Row]:
        sql = "SELECT * FROM ExtractionFolder WHERE normalized_name = ?"
        params: list[Any] = [normalized_name]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        with self.connect() as conn:
            return list(conn.execute(sql, params))

    def get_all_normalized_names(self, exclude_id: int | None = None) -> list[tuple[int, str]]:
        sql = "SELECT id, normalized_name FROM ExtractionFolder"
        params: list[Any] = []
        if exclude_id is not None:
            sql += " WHERE id != ?"
            params.append(exclude_id)
        with self.connect() as conn:
            return [(int(r["id"]), r["normalized_name"]) for r in conn.execute(sql, params)]

    def update_extraction_availability(self, root_id: int, availability: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE ExtractionFolder SET availability = ? WHERE root_id = ?",
                (availability, root_id),
            )

    def update_extraction_catalog(
        self,
        extraction_id: int,
        *,
        original_name: str | None = None,
        normalized_name: str | None = None,
        folder_path: str | None = None,
        folder_type: str | None = None,
        new_folder_name: str | None = None,
        availability: str | None = None,
        reorganize_status: str | None = None,
        notes: str | None = None,
        file_count: int | None = None,
        total_size: int | None = None,
        pre_reorganize_folder_path: str | None = None,
        pre_reorganize_folder_name: str | None = None,
    ) -> None:
        """Update editable catalog fields for one extraction folder."""
        if folder_type is not None and folder_type not in (FOLDER_TYPE_ROOT, FOLDER_TYPE_COLLECTION):
            folder_type = FOLDER_TYPE_COLLECTION
        fields: list[str] = []
        values: list[Any] = []
        mapping = {
            "original_name": original_name,
            "normalized_name": normalized_name,
            "folder_path": folder_path.replace("\\", "/") if folder_path else None,
            "folder_type": folder_type,
            "new_folder_name": new_folder_name,
            "availability": availability,
            "reorganize_status": reorganize_status,
            "notes": notes,
            "file_count": file_count,
            "total_size": total_size,
            "pre_reorganize_folder_path": (
                pre_reorganize_folder_path.replace("\\", "/")
                if pre_reorganize_folder_path
                else None
            ),
            "pre_reorganize_folder_name": pre_reorganize_folder_name,
        }
        for col, val in mapping.items():
            if val is not None:
                fields.append(f"{col} = ?")
                values.append(val)
        if not fields:
            return
        values.append(extraction_id)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE ExtractionFolder SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def delete_extraction(self, extraction_id: int) -> None:
        """Remove extraction folder and its indexed media from the catalog."""
        with self.connect() as conn:
            conn.execute("DELETE FROM Media WHERE extraction_id = ?", (extraction_id,))
            conn.execute("DELETE FROM ExtractionFolder WHERE id = ?", (extraction_id,))

    def update_extraction_fields(
        self,
        extraction_id: int,
        *,
        file_count: int | None = None,
        total_size: int | None = None,
        availability: str | None = None,
    ) -> None:
        fields: list[str] = []
        values: list[Any] = []
        if file_count is not None:
            fields.append("file_count = ?")
            values.append(file_count)
        if total_size is not None:
            fields.append("total_size = ?")
            values.append(total_size)
        if availability is not None:
            fields.append("availability = ?")
            values.append(availability)
        if not fields:
            return
        values.append(extraction_id)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE ExtractionFolder SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def get_extraction_paths_for_root(self, root_id: int) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT folder_path FROM ExtractionFolder WHERE root_id = ?",
                (root_id,),
            ).fetchall()
        return {str(r["folder_path"]).replace("\\", "/") for r in rows}

    def clear_all_catalog_data(self) -> None:
        """Remove all indexed data (keeps schema). Library roots in config are unchanged."""
        with self.connect() as conn:
            for table in (
                "DuplicateMember",
                "DuplicateGroup",
                "NameMatchMember",
                "NameMatchGroup",
                "DownloadHistory",
                "Metadata",
                "Media",
                "Archive",
                "ExtractionFolder",
                "LibraryRoot",
                "StorageDevice",
            ):
                conn.execute(f"DELETE FROM {table}")

    def set_new_folder_name(self, extraction_id: int, new_folder_name: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE ExtractionFolder SET new_folder_name = ? WHERE id = ?",
                (new_folder_name, extraction_id),
            )

    def set_reorganize_status(self, extraction_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE ExtractionFolder
                SET reorganize_status = ?, reorganized_at = ?
                WHERE id = ?
                """,
                (status, _utc_now() if status == "completed" else None, extraction_id),
            )

    def get_extraction(self, extraction_id: int) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT e.*, r.root_path, d.name AS device_name
                FROM ExtractionFolder e
                JOIN LibraryRoot r ON r.id = e.root_id
                JOIN StorageDevice d ON d.id = r.device_id
                WHERE e.id = ?
                """,
                (extraction_id,),
            ).fetchone()

    # --- Media ---
    def upsert_media(
        self,
        root_id: int,
        relative_path: str,
        absolute_path: str,
        original_name: str,
        file_size: int,
        file_type: str,
        extraction_id: int | None = None,
        folder_path: str = "",
        depth: int = 0,
        file_hash: str | None = None,
        mtime: str | None = None,
        status: str = "indexed",
    ) -> int:
        now = _utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO Media (
                    root_id, extraction_id, relative_path, absolute_path, folder_path,
                    depth, original_name, file_hash, file_size, file_type, mtime,
                    availability, status, date_added, last_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'online', ?, ?, ?)
                ON CONFLICT(root_id, relative_path) DO UPDATE SET
                    absolute_path=excluded.absolute_path,
                    file_size=excluded.file_size,
                    file_hash=COALESCE(excluded.file_hash, Media.file_hash),
                    mtime=excluded.mtime,
                    last_verified=excluded.last_verified,
                    status=excluded.status
                """,
                (
                    root_id, extraction_id, relative_path, absolute_path, folder_path,
                    depth, original_name, file_hash, file_size, file_type, mtime,
                    status, now, now,
                ),
            )
            row = conn.execute(
                "SELECT id FROM Media WHERE root_id = ? AND relative_path = ?",
                (root_id, relative_path),
            ).fetchone()
            return int(row["id"])

    def get_media_by_hash(self, file_hash: str) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute("SELECT * FROM Media WHERE file_hash = ?", (file_hash,)))

    def update_media_hash(self, media_id: int, file_hash: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE Media SET file_hash = ? WHERE id = ?", (file_hash, media_id))

    def get_media_in_extraction(self, extraction_id: int) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    "SELECT * FROM Media WHERE extraction_id = ? ORDER BY relative_path",
                    (extraction_id,),
                )
            )

    def find_media_by_relative(self, root_id: int, relative_path: str) -> sqlite3.Row | None:
        rel = relative_path.replace("\\", "/")
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM Media WHERE root_id = ? AND relative_path = ?",
                (root_id, rel),
            ).fetchone()

    def find_media_by_hash_in_extraction(
        self, extraction_id: int, file_hash: str
    ) -> sqlite3.Row | None:
        if not file_hash:
            return None
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM Media
                WHERE extraction_id = ? AND file_hash = ?
                LIMIT 1
                """,
                (extraction_id, file_hash),
            ).fetchone()

    def find_media_for_reorganize(
        self,
        extraction_id: int,
        root_id: int,
        old_relative: str,
        old_absolute: str,
        file_hash: str | None = None,
    ) -> sqlite3.Row | None:
        rel = old_relative.replace("\\", "/")
        row = self.find_media_by_relative(root_id, rel)
        if row is not None:
            return row
        if file_hash:
            row = self.find_media_by_hash_in_extraction(extraction_id, file_hash)
            if row is not None:
                return row
        old_abs = Path(old_absolute)
        with self.connect() as conn:
            for candidate in conn.execute(
                "SELECT * FROM Media WHERE extraction_id = ?",
                (extraction_id,),
            ):
                cand_abs = candidate["absolute_path"]
                if not cand_abs:
                    continue
                try:
                    if Path(cand_abs).resolve() == old_abs.resolve():
                        return candidate
                except OSError:
                    continue
            row = conn.execute(
                """
                SELECT * FROM Media
                WHERE extraction_id = ? AND absolute_path = ?
                """,
                (extraction_id, old_absolute),
            ).fetchone()
            if row is not None:
                return row
            basename = rel.split("/")[-1] if "/" in rel else rel
            candidates = list(
                conn.execute(
                    """
                    SELECT * FROM Media
                    WHERE extraction_id = ? AND (
                        relative_path = ? OR relative_path LIKE ? OR original_name = ?
                    )
                    ORDER BY length(relative_path) DESC
                    LIMIT 1
                    """,
                    (extraction_id, rel, f"%/{basename}", basename),
                )
            )
            return candidates[0] if candidates else None

    def update_media_for_reorganize(
        self,
        media_id: int,
        *,
        relative_path: str,
        absolute_path: str,
        original_name: str,
        file_size: int,
        file_type: str,
        folder_path: str,
        depth: int,
        file_hash: str | None = None,
        mtime: str | None = None,
    ) -> None:
        now = _utc_now()
        rel = relative_path.replace("\\", "/")
        parent = folder_path.replace("\\", "/") if folder_path else ""
        with self.connect() as conn:
            root_row = conn.execute(
                "SELECT root_id FROM Media WHERE id = ?", (media_id,)
            ).fetchone()
            if root_row:
                rid = int(root_row["root_id"])
                conn.execute(
                    "DELETE FROM Metadata WHERE media_id IN ("
                    "SELECT id FROM Media WHERE root_id = ? AND relative_path = ? AND id != ?"
                    ")",
                    (rid, rel, media_id),
                )
                conn.execute(
                    "DELETE FROM Media WHERE root_id = ? AND relative_path = ? AND id != ?",
                    (rid, rel, media_id),
                )
            conn.execute(
                """
                UPDATE Media SET
                    relative_path = ?,
                    absolute_path = ?,
                    original_name = ?,
                    file_size = ?,
                    file_type = ?,
                    folder_path = ?,
                    depth = ?,
                    file_hash = COALESCE(?, file_hash),
                    mtime = COALESCE(?, mtime),
                    availability = 'online',
                    status = 'indexed',
                    last_verified = ?
                WHERE id = ?
                """,
                (
                    rel,
                    absolute_path,
                    original_name,
                    file_size,
                    file_type,
                    parent,
                    depth,
                    file_hash,
                    mtime,
                    now,
                    media_id,
                ),
            )

    def delete_media_ids(self, media_ids: list[int]) -> None:
        if not media_ids:
            return
        placeholders = ",".join("?" for _ in media_ids)
        with self.connect() as conn:
            conn.execute(f"DELETE FROM Metadata WHERE media_id IN ({placeholders})", media_ids)
            conn.execute(f"DELETE FROM Media WHERE id IN ({placeholders})", media_ids)

    # --- Metadata ---
    def upsert_metadata(self, media_id: int, **fields: Any) -> None:
        allowed = {
            "source_url", "source_site", "source_id", "original_filename",
            "download_tool", "download_date", "description", "tags", "notes",
            "custom_fields", "original_details",
        }
        cols = [k for k in fields if k in allowed and fields[k] is not None]
        if not cols:
            return
        values = [fields[c] for c in cols]
        placeholders = ", ".join(cols)
        updates = ", ".join(f"{c}=excluded.{c}" for c in cols)
        with self.connect() as conn:
            conn.execute(
                f"""
                INSERT INTO Metadata (media_id, {placeholders})
                VALUES (?, {", ".join("?" for _ in cols)})
                ON CONFLICT(media_id) DO UPDATE SET {updates}
                """,
                [media_id, *values],
            )

    # --- Name matches ---
    def create_name_match_group(
        self,
        normalized_name: str,
        match_type: str,
        extraction_ids: list[int],
        similarity_score: float | None = None,
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO NameMatchGroup (
                    normalized_name, match_type, similarity_score,
                    member_count, review_status
                ) VALUES (?, ?, ?, ?, 'pending')
                """,
                (normalized_name, match_type, similarity_score, len(extraction_ids)),
            )
            group_id = int(cur.lastrowid)
            for eid in extraction_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO NameMatchMember (group_id, extraction_id) VALUES (?, ?)",
                    (group_id, eid),
                )
            return group_id

    def get_pending_name_match_groups(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT * FROM NameMatchGroup
                    WHERE review_status = 'pending'
                    ORDER BY match_type, normalized_name
                    """
                )
            )

    def get_name_match_members(self, group_id: int) -> list[ExtractionRow]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT e.*, r.label AS root_label, r.root_path, d.name AS device_name
                FROM NameMatchMember m
                JOIN ExtractionFolder e ON e.id = m.extraction_id
                JOIN LibraryRoot r ON r.id = e.root_id
                JOIN StorageDevice d ON d.id = r.device_id
                WHERE m.group_id = ?
                """,
                (group_id,),
            ).fetchall()
        return [
            ExtractionRow(
                id=int(r["id"]),
                root_id=int(r["root_id"]),
                folder_path=r["folder_path"],
                original_name=r["original_name"],
                normalized_name=r["normalized_name"],
                file_count=int(r["file_count"] or 0),
                total_size=int(r["total_size"] or 0),
                availability=r["availability"],
                folder_type=r["folder_type"] or FOLDER_TYPE_ROOT,
                new_folder_name=r["new_folder_name"],
                reorganize_status=r["reorganize_status"] or "pending",
                device_name=r["device_name"],
                root_label=r["root_label"] or "",
                root_path=r["root_path"],
            )
            for r in rows
        ]

    def update_name_match_review(self, group_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE NameMatchGroup SET review_status = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (status, _utc_now(), group_id),
            )

    def clear_pending_groups_for_extraction(self, extraction_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                DELETE FROM NameMatchGroup WHERE id IN (
                    SELECT group_id FROM NameMatchMember WHERE extraction_id = ?
                ) AND review_status = 'pending'
                """,
                (extraction_id,),
            )

    # --- Duplicate groups ---
    def create_duplicate_group(
        self, file_hash: str, file_size: int, media_ids: list[int], source_group_id: int | None = None
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO DuplicateGroup (file_hash, file_size, member_count, source_name_group_id)
                VALUES (?, ?, ?, ?)
                """,
                (file_hash, file_size, len(media_ids), source_group_id),
            )
            gid = int(cur.lastrowid)
            for mid in media_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO DuplicateMember (group_id, media_id) VALUES (?, ?)",
                    (gid, mid),
                )
            return gid

    def log_event(
        self,
        event_type: str,
        old_path: str | None = None,
        new_path: str | None = None,
        media_id: int | None = None,
        extraction_id: int | None = None,
        details: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO DownloadHistory (
                    media_id, extraction_id, event_type, old_path, new_path, timestamp, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (media_id, extraction_id, event_type, old_path, new_path, _utc_now(), details),
            )

    # --- Face UID ---
    def get_all_face_uid_strings(self) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT uid FROM Face_UID").fetchall()
        return {str(r["uid"]) for r in rows}

    def list_face_uids(self) -> list[FaceUidRow]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM Face_UID ORDER BY uid"
            ).fetchall()
        return [self._face_uid_row_from_sqlite(r) for r in rows]

    def get_face_uid(self, record_id: int) -> FaceUidRow | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM Face_UID WHERE id = ?", (record_id,)
            ).fetchone()
        return self._face_uid_row_from_sqlite(row) if row else None

    def find_face_uid_by_nick(
        self, nick_name: str, *, exclude_id: int | None = None
    ) -> FaceUidRow | None:
        nick = nick_name.strip()
        if not nick:
            return None
        sql = """
            SELECT * FROM Face_UID
            WHERE TRIM(nick_name) != ''
              AND LOWER(TRIM(nick_name)) = LOWER(?)
        """
        params: list[Any] = [nick]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        sql += " ORDER BY uid LIMIT 1"
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
        return self._face_uid_row_from_sqlite(row) if row else None

    def find_face_uid_by_uid(self, uid: str) -> FaceUidRow | None:
        uid = uid.strip().upper()
        if not uid:
            return None
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM Face_UID WHERE UPPER(uid) = ? LIMIT 1", (uid,)
            ).fetchone()
        return self._face_uid_row_from_sqlite(row) if row else None

    @staticmethod
    def _face_uid_row_from_sqlite(row: sqlite3.Row) -> FaceUidRow:
        return FaceUidRow(
            id=int(row["id"]),
            uid=str(row["uid"]),
            nick_name=str(row["nick_name"] or ""),
            region=str(row["region"] or ""),
            comments=str(row["comments"] or ""),
            created_at=str(row["created_at"] or ""),
        )

    def insert_face_uid(
        self,
        uid: str,
        nick_name: str = "",
        region: str = "",
        comments: str = "",
    ) -> int:
        uid = uid.strip().upper()
        now = _utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO Face_UID (uid, nick_name, region, comments, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (uid, nick_name.strip(), region.strip(), comments.strip(), now),
            )
            return int(cur.lastrowid)

    def update_face_uid(
        self,
        record_id: int,
        *,
        nick_name: str | None = None,
        region: str | None = None,
        comments: str | None = None,
    ) -> None:
        fields: list[str] = []
        values: list[Any] = []
        if nick_name is not None:
            fields.append("nick_name = ?")
            values.append(nick_name.strip())
        if region is not None:
            fields.append("region = ?")
            values.append(region.strip())
        if comments is not None:
            fields.append("comments = ?")
            values.append(comments.strip())
        if not fields:
            return
        values.append(record_id)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE Face_UID SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def delete_face_uid(self, record_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM Face_UID WHERE id = ?", (record_id,))

    def ensure_config_roots(self, roots: list[Any]) -> None:
        """Register library roots from config if missing."""
        for root_cfg in roots:
            path = Path(root_cfg.path)
            if not path.exists():
                continue
            identifier = str(path.resolve()).lower()[:1] + str(path.drive or path.anchor)
            device = self.get_device_by_identifier(identifier)
            if device:
                device_id = int(device["id"])
            else:
                device_id = self.insert_device(
                    name=root_cfg.device_name,
                    device_type=root_cfg.device_type,
                    identifier=identifier,
                    mount_hint=str(path),
                )
            self.insert_root(device_id, str(path.resolve()), root_cfg.label or root_cfg.device_name)

    def export_to(self, export_path: Path) -> None:
        """Write a consistent snapshot of this catalog to export_path."""
        export_catalog_database(self.path, export_path)

    def import_from(self, import_path: Path) -> None:
        """Replace this catalog with data from import_path."""
        import_catalog_database(import_path, self.path)
        self.reload_schema()

    def reload_schema(self) -> None:
        """Re-run migrations after the database file was replaced on disk."""
        self._init_schema()
