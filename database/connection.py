"""
database/connection.py
Provides a single get_connection() factory for the SQLite database.
All other modules should import from here — never hardcode the DB path.
"""

import sqlite3
from pathlib import Path

# Resolve path relative to this file so it works from any working directory
_DB_PATH = Path(__file__).parent.parent / "data" / "market_intelligence.db"


def get_connection() -> sqlite3.Connection:
    """
    Return a SQLite connection with:
    - Row factory set to sqlite3.Row (access columns by name)
    - Foreign key enforcement enabled
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_path() -> Path:
    """Return the resolved path to the database file."""
    return _DB_PATH
