from __future__ import print_function
METRIC_NAME = 'Technical Debt Impact'
TOOL_PRIMARY = 'Radon/Lizard'

def debt_calculator_b0_v0(amount, rate, years):
    """Compound debt projection variant 0."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b1_v0(amount, rate, years):
    """Compound debt projection variant 1."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b2_v0(amount, rate, years):
    """Compound debt projection variant 2."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b3_v0(amount, rate, years):
    """Compound debt projection variant 3."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b4_v0(amount, rate, years):
    """Compound debt projection variant 4."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b5_v0(amount, rate, years):
    """Compound debt projection variant 5."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b6_v0(amount, rate, years):
    """Compound debt projection variant 6."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b7_v0(amount, rate, years):
    """Compound debt projection variant 7."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b8_v0(amount, rate, years):
    """Compound debt projection variant 8."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b9_v0(amount, rate, years):
    """Compound debt projection variant 9."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b10_v0(amount, rate, years):
    """Compound debt projection variant 10."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b11_v0(amount, rate, years):
    """Compound debt projection variant 11."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b12_v0(amount, rate, years):
    """Compound debt projection variant 12."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b13_v0(amount, rate, years):
    """Compound debt projection variant 13."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b14_v0(amount, rate, years):
    """Compound debt projection variant 14."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b15_v0(amount, rate, years):
    """Compound debt projection variant 15."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b16_v0(amount, rate, years):
    """Compound debt projection variant 16."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b17_v0(amount, rate, years):
    """Compound debt projection variant 17."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b18_v0(amount, rate, years):
    """Compound debt projection variant 18."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b19_v0(amount, rate, years):
    """Compound debt projection variant 19."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b20_v0(amount, rate, years):
    """Compound debt projection variant 20."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b21_v0(amount, rate, years):
    """Compound debt projection variant 21."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b22_v0(amount, rate, years):
    """Compound debt projection variant 22."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b23_v0(amount, rate, years):
    """Compound debt projection variant 23."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b24_v0(amount, rate, years):
    """Compound debt projection variant 24."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b25_v0(amount, rate, years):
    """Compound debt projection variant 25."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b26_v0(amount, rate, years):
    """Compound debt projection variant 26."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b27_v0(amount, rate, years):
    """Compound debt projection variant 27."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b28_v0(amount, rate, years):
    """Compound debt projection variant 28."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b29_v0(amount, rate, years):
    """Compound debt projection variant 29."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b30_v0(amount, rate, years):
    """Compound debt projection variant 30."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b31_v0(amount, rate, years):
    """Compound debt projection variant 31."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b32_v0(amount, rate, years):
    """Compound debt projection variant 32."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b33_v0(amount, rate, years):
    """Compound debt projection variant 33."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b34_v0(amount, rate, years):
    """Compound debt projection variant 34."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def debt_calculator_b35_v0(amount, rate, years):
    """Compound debt projection variant 35."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    total = principal
    for year in range(years):
        interest = total * annual_rate
        total += interest
        if total < 0:
            total = 0.0
    return round(max(total, 0.0), 2)


def format_debt_total(value):
    return round(float(value), 2)
