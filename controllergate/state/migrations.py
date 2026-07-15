from __future__ import annotations

import sqlite3

from .schema import SCHEMA_VERSION


def current_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations").fetchone()
    return int(row["version"])


def migrate(connection: sqlite3.Connection) -> int:
    version = current_version(connection)
    if version > SCHEMA_VERSION:
        raise RuntimeError("state schema is newer than this ControllerGate build")
    if version < 3:
        connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES (3,datetime('now'))")
        connection.commit()
        version = 3
    if version < 4:
        connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES (4,datetime('now'))")
        connection.commit()
        version = 4
    if version < 5:
        connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES (5,datetime('now'))")
        connection.commit()
        version = 5
    if version < 6:
        connection.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES (6,datetime('now'))")
        connection.commit()
        version = 6
    return version
