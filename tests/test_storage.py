from sqlite3 import Connection

from cluecoins.storage import BluecoinsStorage


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
