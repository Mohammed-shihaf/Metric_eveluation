from __future__ import print_function

class WorkflowStep(object):
    def __init__(self, name, handler):
        self.name = name
        self.handler = handler
        self.completed = False

    def run(self, context):
        result = self.handler(context)
        self.completed = True
        return result


class StructuralAnalysisWorkflow(object):
    def __init__(self, repository):
        self.repository = repository
        self._steps = []

    def add_step(self, step):
        self._steps.append(step)

    def run_all(self, snapshot):
        context = {'snapshot': snapshot, 'results': []}
        for step in self._steps:
            context['results'].append(step.run(context))
        return context['results']

    def step_names(self):
        return [step.name for step in self._steps]
