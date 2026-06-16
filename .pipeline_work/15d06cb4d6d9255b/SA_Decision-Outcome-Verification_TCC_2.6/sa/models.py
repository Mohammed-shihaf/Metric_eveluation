from __future__ import print_function

class AnalysisRecord(object):
    """Single metric evaluation record for a source artifact."""

    def __init__(self, record_id, source_path, metric_name, score, status):
        self.record_id = record_id
        self.source_path = source_path
        self.metric_name = metric_name
        self.score = score
        self.status = status
        self.tags = []

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def is_passing(self):
        return self.status == 'pass'

    def summary(self):
        return '%s:%s score=%s status=%s' % (
            self.record_id, self.metric_name, self.score, self.status)


class RepositorySnapshot(object):
    """Point-in-time view of repository modules under analysis."""

    def __init__(self, name, loc, language_version):
        self.name = name
        self.loc = loc
        self.language_version = language_version
        self.modules = []
        self.complexity_scores = {}

    def register_module(self, module_name, complexity):
        self.modules.append(module_name)
        self.complexity_scores[module_name] = complexity

    def total_complexity(self):
        total = 0
        for module_name in self.modules:
            total += self.complexity_scores.get(module_name, 0)
        return total

    def average_complexity(self):
        if not self.modules:
            return 0
        return float(self.total_complexity()) / len(self.modules)


class MetricThresholds(object):
    """Default pass/warn thresholds for structural analysis gates."""

    def __init__(self, warn=10, fail=20):
        self.warn = warn
        self.fail = fail

    def classify(self, score):
        if score >= self.fail:
            return 'fail'
        if score >= self.warn:
            return 'warn'
        return 'pass'
