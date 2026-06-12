from __future__ import print_function
METRIC_NAME = 'Technical Debt Impact'
TOOL_PRIMARY = 'Radon/Lizard'

DOMAIN_NOTES = {
    'owner': 'structural-analysis',
    'module': 'technical_debt',
    'metric': 'Technical Debt Impact',
    'tool': 'Radon/Lizard',
    'reviewed': True,
}


def debt_calculator_stub(amount, rate, years):
    if years < 0 or amount < 0:
        raise ValueError('invalid input')
    total = float(amount)
    for _ in range(years):
        total += total * rate
    return max(total, 0.0)


class DebtSummary(object):
    def __init__(self, items):
        self.items = list(items or [])

    def total(self):
        return sum(self.items)
