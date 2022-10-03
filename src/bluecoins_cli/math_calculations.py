from decimal import Decimal


def get_amount_original(amount: Decimal, rate: Decimal) -> Decimal:
    return amount * rate


def get_amount_quote(amount_original: Decimal, true_rate: Decimal) -> Decimal:
    return amount_original / true_rate
