from datetime import datetime
from decimal import Decimal
from sqlite3 import Connection
from sqlite3 import OperationalError
from typing import TypedDict

import pytest

from cluecoins.storage import BluecoinsStorage
from cluecoins.storage import Storage


def test_create_database(initialization_storage: Storage) -> None:

    try:
        conn = initialization_storage.db

        conn.cursor().execute(
            'SELECT * FROM quotes;',
        )
    except OperationalError:
        raise pytest.fail('Table not exists')


def test_add_quote(initialization_storage: Storage) -> None:
    class QuoteDict(TypedDict):
        date: datetime
        base_currency: str
        quote_currency: str
        price: Decimal

    quote_dict: QuoteDict = {
        'date': datetime(2022, 7, 15),
        'base_currency': 'USDT',
        'quote_currency': 'USD',
        'price': Decimal('1230.23'),
    }

    conn = initialization_storage.db

    initialization_storage.add_quote(**quote_dict)

    quote_data = conn.cursor().execute(
        'SELECT * FROM quotes',
    )
    expected_quote_data = quote_data.fetchall()

    assert expected_quote_data == [('2022-07-15 00:00:00', 'USDT', 'USD', 1230.23)]


def test_get_quote(initialization_storage: Storage) -> None:
    class QuoteDict(TypedDict):
        date: datetime
        base_currency: str
        quote_currency: str
        price: Decimal

    quote_data: QuoteDict = {
        'date': datetime(2022, 7, 15),
        'base_currency': 'USDT',
        'quote_currency': 'USD',
        'price': Decimal('1230.23'),
    }

    initialization_storage.add_quote(**quote_data)

    expected_quote_price = initialization_storage.get_quote(
        date=quote_data['date'], base_currency=quote_data['base_currency'], quote_currency=quote_data['quote_currency']
    )

    assert expected_quote_price == Decimal('1230.23')


def test_create_account(conn: Connection) -> None:

    storage = BluecoinsStorage(conn)
    storage.create_account('Archive', 'USD')

    account_data = conn.cursor().execute(
        'SELECT accountName, accountCurrency FROM ACCOUNTSTABLE WHERE accountName = ?',
        ('Archive',),
    )
    expected_account_data = account_data.fetchone()

    assert expected_account_data == ('Archive', 'USD')


def test_get_account_id(conn: Connection) -> None:

    storage = BluecoinsStorage(conn)
    expected_id = storage.get_account_id('Checking')

    assert expected_id == 1


def test_add_label(conn: Connection) -> None:

    storage = BluecoinsStorage(conn)
    storage.add_label(3, 'clue_test')

    transactions_list = conn.cursor().execute('SELECT * FROM LABELSTABLE WHERE labelName = ?', ('clue_test',))
    expected_transactions_list = len(transactions_list.fetchall())

    assert expected_transactions_list == 526
