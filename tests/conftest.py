import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Iterable

import pytest


@pytest.fixture
def conn() -> Iterable[Connection]:
    """Fixture to set up the in-memory database with test data"""

    conn = sqlite3.connect(':memory:')

    path = Path(__file__).parent / 'test_data.sql'
    sql = path.read_text()
    conn.executescript(sql)

    yield conn
