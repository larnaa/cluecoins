import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Iterable

import pytest

from cluecoins.storage import Storage


@pytest.fixture
def initialization_storage(tmp_path: Path) -> Iterable[Storage]:
    """Fixture to set up the temporary local database"""

    db_path = tmp_path / 'cluecoins' / 'cluecoins.db'
    storage = Storage(db_path)
    storage.create_quote_table()

    yield storage


@pytest.fixture
def conn() -> Iterable[Connection]:
    """Fixture to set up the in-memory Bluecoins database with test data"""

    conn = sqlite3.connect(':memory:')

    path = Path(__file__).parent / 'test_data.sql'
    sql = path.read_text()
    conn.executescript(sql)

    yield conn
