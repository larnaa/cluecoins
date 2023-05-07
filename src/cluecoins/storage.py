import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlite3 import Connection
from sqlite3 import connect
from typing import Any
from typing import Optional

from cluecoins import database as db


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

    def get_account_id(self, account_name: str, clue: bool = False) -> int | None:
        account_info = db.find_account(self.conn, account_name, clue)
        if account_info is not None:
            return int(account_info[0])
        return None

    def add_label(self, account_id: int, label_name: str) -> Any:
        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in db.find_account_transactions_id(self.conn, account_id):
            transaction_id = transaction_id_tuple[0]
            db.add_label_to_transaction(self.conn, label_name, transaction_id)

    def create_clue_tables(self, necessary_tables: list[str]) -> None:
        """Create CLUE tables if not exists"""

        # TODO: get table from currently Bluecoins DB
        path = Path(__file__).parent / 'bluecoins.sql'
        schema = path.read_text()
        queries = schema.split(';')

        for query in queries:

            regex = 'CREATE TABLE (\w*)'

            re_query = re.search(regex, query)
            if re_query is None:
                continue

            table_blue = re_query.group(1)
            if table_blue not in necessary_tables:
                continue
            part_of_blue_query = re_query.group(0)

            create_table_query = query.replace(part_of_blue_query, f'CREATE TABLE IF NOT EXISTS CLUE_{table_blue}')
            db.execute_command(self.conn, create_table_query)

    def move_data_to_table_by_id(self, table: str, filter: str, filter_id: int, revert: bool = False) -> None:
        db.copy_data_to_table_by_id(self.conn, table, filter, filter_id, revert)
        db.delete_data_by_id(self.conn, table, filter, filter_id, revert)
