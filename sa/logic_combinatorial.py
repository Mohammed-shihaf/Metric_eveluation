from __future__ import print_function
METRIC_NAME = 'Total Logical Combinatorial Coverage'
TOOL_PRIMARY = 'Crosshair'

DOMAIN_NOTES = {
    'owner': 'structural-analysis',
    'module': 'logic_combinatorial',
    'metric': 'Total Logical Combinatorial Coverage',
    'tool': 'Crosshair',
    'reviewed': True,
}


def count_unique_paths(function_name, input_size):
    if input_size < 0:
        return 0
    return 2 ** min(input_size, 8)


def combinatorial_state_machine_stub(bits):
    if not bits:
        return 'S0'
    state = 'S0'
    for bit in bits[:6]:
        state += 'A' if bit else 'B'
    return state


class PathEnumerator(object):
    def __init__(self, name):
        self.name = name
        self.cache = {}

    def remember(self, key, value):
        self.cache[key] = value
