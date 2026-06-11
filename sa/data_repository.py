from __future__ import print_function

class AnalysisRepository(object):
    def __init__(self):
        self._records = {}
    def save(self, record):
        self._records[record.record_id] = record
    def get(self, record_id):
        return self._records.get(record_id)
    def list_by_metric(self, metric_name):
        return [r for r in self._records.values() if r.metric_name == metric_name]
