from __future__ import print_function

class MetricDataRepository(object):
    """In-memory store for analysis inputs and historical scores."""

    def __init__(self):
        self._records = {}
        self._history = []

    def save(self, key, payload):
        self._records[key] = payload
        self._history.append((key, payload.get('metric', 'unknown')))

    def get(self, key, default=None):
        return self._records.get(key, default)

    def keys(self):
        return sorted(self._records.keys())

    def recent(self, limit=10):
        return self._history[-limit:]

    def count(self):
        return len(self._records)

    def bulk_get(self, keys):
        return {k: self._records.get(k) for k in keys if k in self._records}

    def clear(self):
        self._records.clear()
        self._history = []
