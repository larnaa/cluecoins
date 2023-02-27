import base64
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlite3 import Connection
from sqlite3 import connect
from typing import Any
from typing import Optional

from cluecoins import database as db
from cluecoins.database import ENCODED_LABEL_PREFIX


class Storage:
    """Create and managing the local SQLite database."""

    def __init__(self, db_path: Path) -> None:
        """Create file with temorary database"""
        self._path = db_path
        self._db: Optional[Connection] = None

    @property
    def db(self) -> Connection:
        if self._db is None:
            self._db = self.connect_to_database()
        return self._db

    def connect_to_database(self) -> Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)
        return connect(self._path)

    def create_quote_table(self) -> None:
        self.db.execute(
            'CREATE TABLE IF NOT EXISTS quotes (date TEXT, base_currency TEXT, quote_currency TEXT, price REAL)'
        )

    def commit(self) -> None:
        self.db.commit()

    def get_quote(self, date: datetime, base_currency: str, quote_currency: str) -> Optional[Decimal]:
        date = datetime.strptime(datetime.strftime(date, '%Y-%m-%d'), '%Y-%m-%d')
        res = self.db.execute(
            'SELECT price FROM quotes WHERE date = ? AND base_currency = ? AND quote_currency = ?',
            (date, base_currency, quote_currency),
        ).fetchone()
        if res:
            return Decimal(str(res[0]))
        return None

    def add_quote(self, date: datetime, base_currency: str, quote_currency: str, price: Decimal) -> None:
        date = datetime.strptime(datetime.strftime(date, '%Y-%m-%d'), '%Y-%m-%d')
        if not self.get_quote(date, base_currency, quote_currency):
            self.db.execute(
                'INSERT INTO quotes (date, base_currency, quote_currency, price) VALUES (?, ?, ?, ?)',
                (date, base_currency, quote_currency, str(price)),
            )


class BluecoinsStorage:
    """Managing the Bluecoins database"""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def create_account(self, account_name: str, account_currency: str) -> bool:
        if db.find_account(self.conn, account_name) is None:
            db.create_new_account(self.conn, account_name, account_currency)
            return True
        return False

    def get_account_id(self, account_name: str) -> int | None:
        account_info = db.find_account(self.conn, account_name)
        if account_info is not None:
            return int(account_info[0])
        return None

    def add_label(self, account_id: int, label_name: str) -> Any:
        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in db.find_account_transactions_id(self.conn, account_id):
            transaction_id = transaction_id_tuple[0]
            db.add_label_to_transaction(self.conn, label_name, transaction_id)

    def encode_account_info(self, account_name: str) -> str | None:

        '''All this is true if the ACCOUNTSTABLE table has a schema:

        CREATE TABLE ACCOUNTSTABLE(
                        accountsTableID INTEGER PRIMARY KEY,
                        accountName VARCHAR(63),
                        accountTypeID INTEGER,
                        accountHidden INTEGER,
                        accountCurrency VARCHAR(5),
                        accountConversionRateNew REAL,
                        currencyChanged INTEGER,
                        creditLimit INTEGER,
                        cutOffDa INTEGER,
                        creditCardDueDate INTEGER,
                        cashBasedAccounts INTEGER,
                        accountSelectorVisibility INTEGER,
                        accountsExtraColumnInt1 INTEGER,
                        accountsExtraColumnInt2 INTEGER,
                        accountsExtraColumnString1 VARCHAR(255),
                        accountsExtraColumnString2 VARCHAR(255)
                    );
        CREATE INDEX 'accountsTable1' ON ACCOUNTSTABLE(accountTypeID);
        '''

        account_info = db.find_account(self.conn, account_name)

        if account_info is None:
            return None

        delimiter = ','
        info: str = delimiter.join([str(value) for value in account_info])

        info_bytes = info.encode("utf-8")

        base64_bytes = base64.b64encode(info_bytes)
        account_info_base64 = base64_bytes.decode("utf-8")

        return account_info_base64

    def decode_account_info(self, account_name: str) -> tuple[Any, ...]:
        label_name = f'clue_{account_name}'
        transaction_id = db.find_transactions_by_label(self.conn, label_name)[0][0]

        labels_list = db.find_labels_by_transaction_id(self.conn, transaction_id)

        for label in labels_list:
            if not label[0].startswith(ENCODED_LABEL_PREFIX):
                continue

            label_parts = label[0].split('_')
            account_info_base64 = label_parts[-1]

            base64_bytes = account_info_base64.encode('utf-8')

            sample_string_bytes = base64.b64decode(base64_bytes)
            sample_string: str = sample_string_bytes.decode('utf-8')

            account_info_tuple = tuple(sample_string.split(','))

        account_info_list: list[str | None] = list(account_info_tuple)

        for i, info in enumerate(account_info_list):
            if info == 'None':
                account_info_list[i] = None

        account_info_list.pop(0)
        account_info = tuple(account_info_list)
        return account_info
