from datetime import datetime
from decimal import Decimal
from sqlite3 import Connection

from cluecoins.database import add_label_to_transaction
from cluecoins.database import create_new_account
from cluecoins.database import delete_account
from cluecoins.database import find_account
from cluecoins.database import find_account_transactions_id
from cluecoins.database import get_accounts_list
from cluecoins.database import get_base_currency
from cluecoins.database import iter_accounts
from cluecoins.database import iter_transactions
from cluecoins.database import move_transactions_to_account
from cluecoins.database import set_base_currency
from cluecoins.database import update_account
from cluecoins.database import update_transaction


def test_set_base_currency(conn: Connection) -> None:

    set_base_currency(conn, 'UYU')

    base_currency = conn.cursor().execute('SELECT defaultSettings FROM SETTINGSTABLE WHERE settingsTableID = ?', (1,))
    expected_base_currency = base_currency.fetchone()[0]

    assert expected_base_currency == 'UYU'


def test_get_base_currency(conn: Connection) -> None:

    expected_base_currency = get_base_currency(conn)

    assert expected_base_currency == 'USD'


def test_iter_transactions(conn: Connection) -> None:

    expected_transaction_data = next(iter_transactions(conn))

    assert expected_transaction_data == (datetime(2049, 8, 6, 11, 50), 13279, Decimal('1.0'), 'USD', Decimal('469'))


def test_iter_accounts(conn: Connection) -> None:

    expected_account_data = next(iter_accounts(conn, 'USD', 'USDT'))

    assert expected_account_data == (-1, 'USDT', Decimal('1.0'))


def test_get_account_list(conn: Connection) -> None:

    account_list = get_accounts_list(conn)
    expected_len_account_list = len(account_list)

    assert expected_len_account_list == 10


def test_update_account(conn: Connection) -> None:

    update_account(conn, 1, Decimal(0.123))
    account_conversion_rate_new = conn.cursor().execute(
        'SELECT accountConversionRateNew FROM ACCOUNTSTABLE WHERE accountsTableID = ?', (1,)
    )
    expected_account_conversion_rate_new = account_conversion_rate_new.fetchone()[0]

    assert expected_account_conversion_rate_new == 0.123


def test_find_account(conn: Connection) -> None:
    # TODO: add an account within this function

    account = find_account(conn, 'Visa')
    expected_account = account[1]

    assert expected_account == 'Visa'


def test_create_new_account(conn: Connection) -> None:

    create_new_account(conn, 'FTX', 'USD')

    account = conn.cursor().execute(
        'SELECT * FROM ACCOUNTSTABLE WHERE accountName = ?',
        ('FTX',),
    )
    expected_account_name = account.fetchone()[1]

    assert expected_account_name == 'FTX'


def test_delete_account(conn: Connection) -> None:
    # TODO: add and delete an account within this function

    delete_account(conn, 1)

    account = conn.cursor().execute(
        'SELECT * FROM ACCOUNTSTABLE WHERE accountsTableID = ?',
        (1,),
    )
    expected_account = account.fetchall()

    assert expected_account == []


def test_add_label_to_transactions(conn: Connection) -> None:

    add_label_to_transaction(conn, 'clue_test', 5000)

    label = conn.cursor().execute(
        'SELECT * FROM LABELSTABLE WHERE transactionIDLabels = ?',
        (5000,),
    )
    expectes_label = label.fetchone()[1]

    assert expectes_label == 'clue_test'


def test_find_account_transactions_id(conn: Connection) -> None:

    transactions_id_list = find_account_transactions_id(conn, 1).fetchall()
    expected_transactions_id_account_list = len(transactions_id_list)

    assert expected_transactions_id_account_list == 823


def test_update_transaction(conn: Connection) -> None:

    update_transaction(conn, 5005, Decimal(10), Decimal(1))

    update_data_tuple = conn.cursor().execute(
        'SELECT conversionRateNew, amount FROM TRANSACTIONSTABLE WHERE transactionsTableID = ?',
        (5005,),
    )
    expected_update_data_tuple = update_data_tuple.fetchone()

    assert expected_update_data_tuple == (10.0, 1000000)


def test_move_transactions_to_account(conn: Connection) -> None:

    move_transactions_to_account(conn, 4, 5)

    transactions_list = conn.cursor().execute(
        'SELECT * FROM TRANSACTIONSTABLE WHERE accountID = 5',
    )
    expected_transactions_list = len(transactions_list.fetchall())

    assert expected_transactions_list == 292
