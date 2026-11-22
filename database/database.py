"""Security/database owner: future SQLite connection and transaction management.
The current runnable store is MockRepository in database/repository.py.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from database.models import SCHEMA

@contextmanager
def connect(db_path):
    path = Path(db_path)
    if str(path) == ':memory:':
        raise ValueError('Use a file-backend SQLite path for per-operation connection')
    connection = sqlite3.connect(str(path), timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('PRAGMA foreign_keys = ON')
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize_database(db_path):
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
