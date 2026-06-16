from __future__ import print_function

class StructuralRule(object):
    def __init__(self, rule_id, description, severity):
        self.rule_id = rule_id
        self.description = description
        self.severity = severity

    def applies_to(self, module_name):
        return module_name.startswith('sa.')


class RulesEngine(object):
    def __init__(self):
        self._rules = []

    def register(self, rule):
        self._rules.append(rule)

    def evaluate(self, module_name):
        matched = []
        for rule in self._rules:
            if rule.applies_to(module_name):
                matched.append(rule.rule_id)
        return matched

    def rule_count(self):
        return len(self._rules)

    def rule_ids(self):
        return [rule.rule_id for rule in self._rules]
