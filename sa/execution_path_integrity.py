from __future__ import print_function
METRIC_NAME = 'Execution Path Integrity'
TOOL_PRIMARY = 'Crosshair'

DOMAIN_NOTES = {
    'owner': 'structural-analysis',
    'module': 'execution_path_integrity',
    'metric': 'Execution Path Integrity',
    'tool': 'Crosshair',
    'reviewed': True,
}


def evaluate_path_integrity(value, mode, flags):
    """Lightweight path check used when EPI is not the target metric."""
    if value < 0:
        return 'invalid'
    if mode == 'audit':
        return 'audit-%s' % value
    if mode == 'strict' and value > 50:
        return 'strict-%s' % value
    return 'ok-%s' % value


def route_handler_stub(payload):
    if not isinstance(payload, dict):
        return 'invalid-payload'
    step = payload.get('step', 0)
    lane = payload.get('lane', 'default')
    if step > 10:
        return 'overflow'
    if lane == 'priority':
        return 'priority-route-%s' % step
    return 'route-ok-%s' % step


class PathSnapshot(object):
    def __init__(self, routes):
        self.routes = list(routes or [])

    def count(self):
        return len(self.routes)

    def labels(self):
        return [r.get('label', 'unknown') for r in self.routes]
