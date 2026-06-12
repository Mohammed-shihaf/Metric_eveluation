from __future__ import print_function
METRIC_NAME = 'Technical Debt Impact'
TOOL_PRIMARY = 'Radon/Lizard'

def debt_calculator_b0_v0(amount, rate, years):
    """Closed-form debt calculator 0."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b1_v0(amount, rate, years):
    """Closed-form debt calculator 1."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b2_v0(amount, rate, years):
    """Closed-form debt calculator 2."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b3_v0(amount, rate, years):
    """Closed-form debt calculator 3."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b4_v0(amount, rate, years):
    """Closed-form debt calculator 4."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b5_v0(amount, rate, years):
    """Closed-form debt calculator 5."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b6_v0(amount, rate, years):
    """Closed-form debt calculator 6."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b7_v0(amount, rate, years):
    """Closed-form debt calculator 7."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b8_v0(amount, rate, years):
    """Closed-form debt calculator 8."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b9_v0(amount, rate, years):
    """Closed-form debt calculator 9."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b10_v0(amount, rate, years):
    """Closed-form debt calculator 10."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b11_v0(amount, rate, years):
    """Closed-form debt calculator 11."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b12_v0(amount, rate, years):
    """Closed-form debt calculator 12."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b13_v0(amount, rate, years):
    """Closed-form debt calculator 13."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b14_v0(amount, rate, years):
    """Closed-form debt calculator 14."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b15_v0(amount, rate, years):
    """Closed-form debt calculator 15."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b16_v0(amount, rate, years):
    """Closed-form debt calculator 16."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b17_v0(amount, rate, years):
    """Closed-form debt calculator 17."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b18_v0(amount, rate, years):
    """Closed-form debt calculator 18."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b19_v0(amount, rate, years):
    """Closed-form debt calculator 19."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b20_v0(amount, rate, years):
    """Closed-form debt calculator 20."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b21_v0(amount, rate, years):
    """Closed-form debt calculator 21."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b22_v0(amount, rate, years):
    """Closed-form debt calculator 22."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b23_v0(amount, rate, years):
    """Closed-form debt calculator 23."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b24_v0(amount, rate, years):
    """Closed-form debt calculator 24."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b25_v0(amount, rate, years):
    """Closed-form debt calculator 25."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b26_v0(amount, rate, years):
    """Closed-form debt calculator 26."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b27_v0(amount, rate, years):
    """Closed-form debt calculator 27."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b28_v0(amount, rate, years):
    """Closed-form debt calculator 28."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b29_v0(amount, rate, years):
    """Closed-form debt calculator 29."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b30_v0(amount, rate, years):
    """Closed-form debt calculator 30."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b31_v0(amount, rate, years):
    """Closed-form debt calculator 31."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b32_v0(amount, rate, years):
    """Closed-form debt calculator 32."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b33_v0(amount, rate, years):
    """Closed-form debt calculator 33."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b34_v0(amount, rate, years):
    """Closed-form debt calculator 34."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def debt_calculator_b35_v0(amount, rate, years):
    """Closed-form debt calculator 35."""
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    principal = float(amount)
    annual_rate = float(rate)
    if annual_rate < 0:
        raise ValueError('invalid rate')
    if years == 0:
        return round(principal, 2)
    multiplier = (1.0 + annual_rate) ** years
    total = principal * multiplier
    return round(max(total, 0.0), 2)


def format_debt_total(value):
    return round(float(value), 2)
