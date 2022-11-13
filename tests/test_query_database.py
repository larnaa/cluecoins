import sqlite3
from decimal import Decimal
from pathlib import Path
from sqlite3 import Connection
from typing import Iterable

import pytest

from cluecoins.database import add_label_to_transaction
from cluecoins.database import create_new_account
from cluecoins.database import delete_account
from cluecoins.database import find_account
from cluecoins.database import find_account_transactions_id
from cluecoins.database import get_account_list
from cluecoins.database import get_base_currency
from cluecoins.database import set_base_currency
from cluecoins.database import update_account


@pytest.fixture
def create_memory_db() -> Iterable[Connection]:
    """Fixture to set up the in-memory database with test data"""

    conn = sqlite3.connect(':memory:')

    path = Path(__file__).parent / 'test_data.sql'
    sql = path.read_text()
    conn.executescript(sql)

    yield conn


def test_set_base_currency(create_memory_db: Connection) -> None:

    conn = create_memory_db
    set_base_currency(conn, 'UYU')

    base_currency = conn.cursor().execute('SELECT defaultSettings FROM SETTINGSTABLE WHERE settingsTableID = ?', (1,))
    expected_base_currency = base_currency.fetchone()[0]

    assert expected_base_currency == 'UYU'


def test_get_base_currency(create_memory_db: Connection) -> None:

    conn = create_memory_db
    expected_base_currency = get_base_currency(conn)

    assert expected_base_currency == 'USD'


def test_get_account_list(create_memory_db: Connection) -> None:

    conn = create_memory_db
    account_list = get_account_list(conn)
    expected_len_account_list = len(account_list)

    assert expected_len_account_list == 10


def test_update_account(create_memory_db: Connection) -> None:

    conn = create_memory_db
    update_account(conn, 1, Decimal(0.123))
    account_conversion_rate_new = conn.cursor().execute(
        'SELECT accountConversionRateNew FROM ACCOUNTSTABLE WHERE accountsTableID = ?', (1,)
    )
    expected_account_conversion_rate_new = account_conversion_rate_new.fetchone()[0]

    assert expected_account_conversion_rate_new == 0.123


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


def test_add_label_to_transactions(create_memory_db: Connection) -> None:

    conn = create_memory_db
    add_label_to_transaction(conn, 'clue_test', 5000)

    label = conn.cursor().execute(
        'SELECT * FROM LABELSTABLE WHERE transactionIDLabels = ?',
        (5000,),
    )
    expectes_label = label.fetchone()[1]

    assert expectes_label == 'clue_test'


def test_find_account_transactions_id(create_memory_db: Connection) -> None:

    conn = create_memory_db
    transactions_id_list = find_account_transactions_id(conn, 1).fetchall()
    expected_transactions_id_account_list = len(transactions_id_list)

    assert expected_transactions_id_account_list == 823
