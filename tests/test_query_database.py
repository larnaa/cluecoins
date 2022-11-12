import sqlite3
from sqlite3 import Connection
import pytest
from pathlib import Path

from cluecoins.database import create_new_account

@pytest.fixture
def create_memory_db() -> Connection:
    """ Fixture to set up the in-memory database with test data """

    conn = sqlite3.connect(':memory:')

    path = Path(__file__).parent / 'test_data.sql'
    sql = path.read_text()
    conn.executescript(sql)

    yield conn
    

def test_create_new_account(create_memory_db: Connection):

    conn = create_memory_db
    cursor = conn.cursor()

    create_new_account(conn, 'FTX', 'USD')
    account = cursor.execute(
        'SELECT * FROM ACCOUNTSTABLE WHERE accountName = ?',
        ('FTX',),
    )
    expected_account_name = account.fetchone()[1]

    assert expected_account_name == 'FTX'

