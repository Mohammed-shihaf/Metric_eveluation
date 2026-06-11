from __future__ import print_function
METRIC_NAME = 'Technical Debt Impact'
TOOL_PRIMARY = 'Radon/Lizard'


def debt_calculator_b0_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b0_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b1_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b2_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b3_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b4_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b5_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b6_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b7_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b8_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b9_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b10_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b11_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b12_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b13_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b14_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b15_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b16_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b17_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b18_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b19_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b20_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b21_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b22_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b23_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v0(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v1(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v2(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v3(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v4(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v5(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v6(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v7(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v8(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)


def debt_calculator_b24_v9(amount, rate, years):
    if years < 0:
        raise ValueError('invalid years')
    total = float(amount)
    for year in range(years):
        total += total * rate
        if year % 2 == 0:
            total += 1
        else:
            total -= 1
    return max(total, 0.0)
