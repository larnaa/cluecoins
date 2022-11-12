import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Generator

import pytest

from cluecoins.database import create_new_account
from cluecoins.database import delete_account
from cluecoins.database import find_account
from cluecoins.database import get_base_currency
from cluecoins.database import set_base_currency


@pytest.fixture
def create_memory_db() -> Generator[Connection]:
    """Fixture to set up the in-memory database with test data"""

    conn = sqlite3.connect(':memory:')

    path = Path(__file__).parent / 'test_data.sql'
    sql = path.read_text()
    conn.executescript(sql)

    yield conn


def test_set_base_currency(create_memory_db: Connection) -> None:
    # TODO: check current currency ?

    conn = create_memory_db
    set_base_currency(conn, 'UYU')

    base_currency = conn.cursor().execute(
        'SELECT defaultSettings FROM SETTINGSTABLE WHERE settingsTableID = "1"',
    )
    expected_base_currency = base_currency.fetchone()[0]

    assert expected_base_currency == 'UYU'


def test_get_base_currency(create_memory_db: Connection) -> None:

    conn = create_memory_db
    expected_base_currency = get_base_currency(conn)

    assert expected_base_currency == 'USD'


def test_find_account(create_memory_db: Connection) -> None:
    # TODO: add an account within this function

    conn = create_memory_db
    account = find_account(conn, 'Visa')
    expected_account = account[1]

    assert expected_account == 'Visa'


def test_create_new_account(create_memory_db: Connection) -> None:

    conn = create_memory_db
    create_new_account(conn, 'FTX', 'USD')

    account = conn.cursor().execute(
        'SELECT * FROM ACCOUNTSTABLE WHERE accountName = ?',
        ('FTX',),
    )
    expected_account_name = account.fetchone()[1]

    assert expected_account_name == 'FTX'


def test_delete_account(create_memory_db: Connection) -> None:
    # TODO: add and delete an account within this function

    conn = create_memory_db
    delete_account(conn, 1)

    account = conn.cursor().execute(
        'SELECT * FROM ACCOUNTSTABLE WHERE accountsTableID = ?',
        (1,),
    )
    expected_account = account.fetchall()

    assert expected_account == []
