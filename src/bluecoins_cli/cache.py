import json
import os
from datetime import datetime
from decimal import Decimal
from os.path import isfile
from typing import Dict

from aiohttp import ClientSession


class QuoteCache:
    def __init__(self, path: str) -> None:
        self._path = path
        self.quotes: Dict[str, Decimal] = {}

    def save(self) -> None:
        if not isfile(self._path):
            os.makedirs(os.path.dirname(self._path), exist_ok=True)

        with open(self._path, 'w') as f:
            json.dump({k: str(v) for k, v in self.quotes.items()}, f)

    def load(self) -> None:
        if isfile(self._path):
            with open(self._path, 'r') as f:
                self.quotes = json.load(f)
        else:
            self.quotes = {}

    async def get_price(self, date: datetime, base_currency: str, quote_currency: str) -> Decimal:
        if base_currency == quote_currency:
            return Decimal('1')

        async with ClientSession('https://api.exchangerate.host') as session:
            short_date = date.strftime('%Y-%m-%d')
            key = f'{short_date}{base_currency}{quote_currency}'

            if key in self.quotes:
                return Decimal(self.quotes[key])

            response = await session.get(
                url='/timeseries',
                params={
                    'start_date': datetime(date.year, 1, 1).strftime('%Y-%m-%d'),
                    'end_date': datetime(date.year, 12, 31).strftime('%Y-%m-%d'),
                    'base': base_currency,
                    'symbols': [quote_currency],
                },
            )
            response_json = await response.json()
            for date, items in response_json['rates'].items():
                for currency, rate in items.items():
                    rate = Decimal(str(rate))
                    curr_key = f'{date}{base_currency}{currency}'
                    self.quotes[curr_key] = rate

            return Decimal(self.quotes[key])
