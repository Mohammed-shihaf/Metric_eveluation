from __future__ import print_function

class AnalysisRecord(object):
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
class WorkflowContext(object):
    def __init__(self, workflow_id, operator):
        self.workflow_id = workflow_id
        self.operator = operator
        self.steps_completed = []
        self.errors = []
        self.metadata = {}
    def mark_step(self, step_name):
        self.steps_completed.append(step_name)
    def add_error(self, message):
        self.errors.append(message)
    def has_errors(self):
        return len(self.errors) > 0

def build_default_tags(tags=None):
    if tags is None:
        tags = []
    tags.append('generated')
    return tags
