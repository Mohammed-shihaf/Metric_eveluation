"""
Generate SA metric branch codebases (SA_<METRIC>_<TYPE>_2.6).

Each branch targets >= 1000 lines in sa/*.py + tests/*.py + main.py (sa/config.py included).
No harness markers: TOOL_MODE, -tcc-, fallback-cc-, if False:, phantom.
"""

from __future__ import print_function

import os
import textwrap

FUTURE = "from __future__ import print_function\n"
N_FUNCTIONS_BY_METRIC = {
    "EPI": 26,
    "DOV": 20,
    "LSV": 32,
    "TLCC": 34,
    "TDI": 36,
    "QRA": 40,
}
MIN_LOC = 1000  # enforced at generation time


def n_functions(abbrev):
    return N_FUNCTIONS_BY_METRIC[abbrev]
FORBIDDEN_MARKERS = ("TOOL_MODE", "-tcc-", "fallback-cc-", "if False:", "phantom")

# module_key -> (abbrev, metric_name, tool, classification)
METRIC_META = {
    "execution_path_integrity": ("EPI", "Execution Path Integrity", "Crosshair", "Static Analysis Metric"),
    "decision_coverage": ("DOV", "Decision Outcome Verification", "Coverage.py", "Decision Coverage"),
    "condition_coverage": ("LSV", "Logical Sub-expression Validation", "Pymcdc", "Condition Coverage"),
    "logic_combinatorial": ("TLCC", "Total Logical Combinatorial Coverage", "Crosshair", "Logic Coverage Metric"),
    "technical_debt": ("TDI", "Technical Debt Impact", "Radon/Lizard", "Maintainability Analysis"),
    "qa_prioritization": ("QRA", "QA Resource Allocation", "testmon", "Test Prioritization"),
}

ABBREV_TO_MODULE = {v[0]: k for k, v in METRIC_META.items()}
MODULE_KEYS = list(METRIC_META.keys())

SA_METRICS_ROWS = [
    (mk, METRIC_META[mk][0], METRIC_META[mk][3], METRIC_META[mk][1], METRIC_META[mk][2])
    for mk in MODULE_KEYS
]


def _assert_no_forbidden(content, path_hint=""):
    for marker in FORBIDDEN_MARKERS:
        if marker in content:
            raise ValueError("Forbidden marker %r in %s" % (marker, path_hint or "generated content"))


def _hdr(metric_name, tool_primary, extra=""):
    lines = [FUTURE, "METRIC_NAME = '%s'\n" % metric_name, "TOOL_PRIMARY = '%s'\n" % tool_primary]
    if extra:
        lines.append(extra)
    lines.append("\n")
    return "".join(lines)


# ---------------------------------------------------------------------------
# Shared support / stub modules (identical across Bug/BugFX/TCC/CC per combo)
# ---------------------------------------------------------------------------

def gen_init_py():
    return FUTURE + textwrap.dedent(
        '''
        """Structural Analysis package for Python 2.6."""

        __version__ = '2.0.0'
        __testing_type__ = 'Structural Analysis'

        SUPPORTED_PYTHON = ('2.6',)

        def package_info():
            return {
                'version': __version__,
                'testing_type': __testing_type__,
                'python': SUPPORTED_PYTHON,
            }
        '''
    )


def gen_config_py(abbrev, branch_type, version="2.6", language="python"):
    metric_name = METRIC_META[ABBREV_TO_MODULE[abbrev]][1]
    tools = "\n".join(
        "    '%s': {'classification': '%s', 'metric': '%s', 'tool': '%s'}," % (mk, meta[3], meta[1], meta[2])
        for mk, meta in METRIC_META.items()
    )
    return FUTURE + (
        '"""Runtime configuration for metric-scoped Structural Analysis."""\n'
        "LANGUAGE = '%(language)s'\n"
        "PYTHON_VERSION = '%(version)s'\n"
        "BRANCH_TYPE = '%(branch_type)s'\n"
        "BRANCH_VARIANT = '%(branch_type)s'\n"
        "TARGET_METRIC_ABBREV = '%(abbrev)s'\n"
        "TARGET_METRIC_NAME = '%(metric)s'\n"
        "TESTING_TYPE = 'Structural Analysis'\n"
        "METRIC_TOOL_MAP = {\n%(tools)s\n}\n"
    ) % {
        "language": language,
        "version": version,
        "branch_type": branch_type,
        "abbrev": abbrev,
        "metric": metric_name,
        "tools": tools,
    }


def gen_models_py():
    return FUTURE + textwrap.dedent(
        '''
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
        '''
    )


def gen_data_repository_py():
    return FUTURE + textwrap.dedent(
        '''
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
        '''
    )


def gen_reporting_py():
    return FUTURE + textwrap.dedent(
        '''
        class MetricReportBuilder(object):
            """Format analysis summaries for console or gate export."""

            def __init__(self, title):
                self.title = title
                self.sections = []

            def add_section(self, name, rows):
                self.sections.append((name, list(rows)))

            def render_text(self):
                lines = [self.title, '=' * len(self.title)]
                for name, rows in self.sections:
                    lines.append('')
                    lines.append(name)
                    lines.append('-' * len(name))
                    for row in rows:
                        lines.append('  %s' % row)
                return '\\n'.join(lines)

            def section_count(self):
                return len(self.sections)

            def row_count(self):
                total = 0
                for _, rows in self.sections:
                    total += len(rows)
                return total
        '''
    )


def gen_rules_engine_py():
    return FUTURE + textwrap.dedent(
        '''
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
        '''
    )


def gen_signal_processing_py():
    return FUTURE + textwrap.dedent(
        '''
        def normalize_signal_batch(readings):
            """Scale raw sensor readings into a stable 0..1 range."""
            if not readings:
                return []
            peak = max(abs(r) for r in readings) or 1.0
            return [round(float(r) / peak, 4) for r in readings]


        def detect_threshold_crossings(readings, threshold):
            crossings = []
            for idx, value in enumerate(readings):
                if value >= threshold:
                    crossings.append(idx)
            return crossings


        class SignalWindow(object):
            def __init__(self, size):
                self.size = size
                self.buffer = []

            def push(self, value):
                self.buffer.append(value)
                if len(self.buffer) > self.size:
                    self.buffer.pop(0)

            def average(self):
                if not self.buffer:
                    return 0.0
                return sum(self.buffer) / float(len(self.buffer))

            def max_value(self):
                if not self.buffer:
                    return 0.0
                return max(self.buffer)
        '''
    )


def gen_integration_hub_py():
    return FUTURE + textwrap.dedent(
        '''
        class IntegrationEndpoint(object):
            def __init__(self, name, base_url):
                self.name = name
                self.base_url = base_url
                self.last_status = 'idle'
                self.retry_count = 0

            def mark_success(self):
                self.last_status = 'ok'
                self.retry_count = 0

            def mark_failure(self, reason):
                self.last_status = 'error:%s' % reason
                self.retry_count += 1

            def should_retry(self, limit=3):
                return self.retry_count < limit


        class IntegrationHub(object):
            def __init__(self):
                self._endpoints = {}

            def register(self, endpoint):
                self._endpoints[endpoint.name] = endpoint

            def get(self, name):
                return self._endpoints.get(name)

            def healthy_count(self):
                return sum(1 for ep in self._endpoints.values() if ep.last_status == 'ok')

            def list_names(self):
                return sorted(self._endpoints.keys())
        '''
    )


def gen_workflow_orchestrator_py():
    return FUTURE + textwrap.dedent(
        '''
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
        '''
    )


def _stub_metric_module(module_key):
    """Non-target metric module: modest realistic helpers (~45-55 lines)."""
    meta = METRIC_META[module_key]
    metric_name, tool = meta[1], meta[2]
    bodies = {
        "execution_path_integrity": textwrap.dedent(
            '''
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
            '''
        ),
        "decision_coverage": textwrap.dedent(
            '''
            def aggregate_decision_coverage(cases):
                if not cases:
                    return 1.0
                covered = sum(1 for c in cases if c.get('covered'))
                return float(covered) / len(cases)


            def decision_case_stub(state, enabled, retry_count, priority):
                if state == 'ready' and enabled:
                    return 'started-stub'
                if state == 'failed':
                    return 'failed-stub'
                if retry_count > 3:
                    return 'retry-stub'
                return 'unknown-stub'


            class DecisionAuditTrail(object):
                def __init__(self):
                    self.events = []

                def record(self, name, outcome):
                    self.events.append((name, outcome))

                def last_outcome(self):
                    return self.events[-1][1] if self.events else None
            '''
        ),
        "condition_coverage": textwrap.dedent(
            '''
            def condition_check_stub(a, b, c, d, flag):
                if flag and ((a and b) or (c and not d)):
                    return 'accept-stub'
                if (a or b) and c:
                    return 'partial-stub'
                if not flag and (a or c):
                    return 'review-stub'
                return 'reject-stub'


            def validate_all_conditions(inputs):
                results = []
                for item in inputs:
                    results.append(condition_check_stub(
                        item.get('a'), item.get('b'), item.get('c'),
                        item.get('d'), item.get('flag')))
                return results


            class ConditionMatrix(object):
                def __init__(self, rows):
                    self.rows = list(rows or [])

                def accepted(self):
                    return [r for r in self.rows if r.endswith('accept')]
            '''
        ),
        "logic_combinatorial": textwrap.dedent(
            '''
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
            '''
        ),
        "technical_debt": textwrap.dedent(
            '''
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
            '''
        ),
        "qa_prioritization": textwrap.dedent(
            '''
            def prioritize_test_bucket_stub(modules, history):
                history = history or {}
                ranking = []
                for module in modules:
                    name = module.get('name', 'unknown')
                    score = module.get('complexity', 0) + history.get(name, 0)
                    bucket = 'high' if score > 10 else 'low'
                    ranking.append((name, bucket))
                return ranking


            class BucketPlanner(object):
                def __init__(self):
                    self.plan = []

                def add(self, name, bucket):
                    self.plan.append((name, bucket))
            '''
        ),
    }
    notes = (
        "DOMAIN_NOTES = {\n"
        "    'owner': 'structural-analysis',\n"
        "    'module': '%s',\n"
        "    'metric': '%s',\n"
        "    'tool': '%s',\n"
        "    'reviewed': True,\n"
        "}\n\n"
    ) % (module_key, metric_name, tool)
    return _hdr(metric_name, tool) + notes + bodies[module_key]


SUPPORT_GENERATORS = {
    "sa/__init__.py": gen_init_py,
    "sa/models.py": gen_models_py,
    "sa/data_repository.py": gen_data_repository_py,
    "sa/reporting.py": gen_reporting_py,
    "sa/rules_engine.py": gen_rules_engine_py,
    "sa/signal_processing.py": gen_signal_processing_py,
    "sa/integration_hub.py": gen_integration_hub_py,
    "sa/workflow_orchestrator.py": gen_workflow_orchestrator_py,
}


# ---------------------------------------------------------------------------
# Target module generators — same N_FUNCTIONS and signatures per metric
# ---------------------------------------------------------------------------

def _normalize_inputs_block(i):
    return (
        "    if not isinstance(state, basestring):\n"
        "        return 'invalid-input-%d'\n"
        "    normalized_state = state.strip().lower()\n"
        "    if not normalized_state:\n"
        "        return 'empty-state-%d'\n"
        "    retry_budget = max(retry_count, 0)\n"
        "    priority_level = max(priority, 0)\n"
        "    enabled_flag = bool(enabled)\n"
    ) % (i, i)


def _dov_outcomes_bugfx(i):
    return (
        "def decision_case_%d(state, enabled, retry_count, priority):\n"
        '    """Evaluate workflow decision case %d."""\n'
        "%s"
        "    if normalized_state == 'ready' and enabled_flag:\n"
        "        if retry_budget > 3:\n"
        "            return 'retry-exhausted-%d'\n"
        "        return 'started-%d'\n"
        "    if normalized_state == 'failed':\n"
        "        return 'failed-%d'\n"
        "    if normalized_state == 'queued' and priority_level > 5:\n"
        "        return 'priority-%d'\n"
        "    return 'unknown-%d'\n"
    ) % (i, i, _normalize_inputs_block(i), i, i, i, i, i)


def _dov_outcomes_bug(i):
    base = _dov_outcomes_bugfx(i)
    extra = (
        "    if normalized_state == 'queued' and priority_level > 9:\n"
        "        return 'escalated-%d'\n"
    ) % i
    # Insert extra uncovered branch before final return
    return base.replace(
        "    return 'unknown-%d'\n" % i,
        extra + "    return 'unknown-%d'\n" % i,
    )


def _dov_outcomes_tcc(i):
    return (
        "def decision_case_%d(state, enabled, retry_count, priority):\n"
        '    """Branch-ladder decision case %d for coverage analysis."""\n'
        "%s"
        "    if normalized_state == 'ready':\n"
        "        if enabled_flag:\n"
        "            if retry_budget > 3:\n"
        "                return 'retry-exhausted-%d'\n"
        "            return 'started-%d'\n"
        "        return 'disabled-%d'\n"
        "    if normalized_state == 'failed':\n"
        "        return 'failed-%d'\n"
        "    if normalized_state == 'queued':\n"
        "        if priority_level > 5:\n"
        "            return 'priority-%d'\n"
        "        return 'queued-%d'\n"
        "    return 'unknown-%d'\n"
    ) % (i, i, _normalize_inputs_block(i), i, i, i, i, i, i, i)


def _dov_outcomes_cc(i):
    return (
        "def decision_case_%d(state, enabled, retry_count, priority):\n"
        '    """Table-assisted decision case %d."""\n'
        "%s"
        "    lookup_key = (normalized_state, enabled)\n"
        "    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')\n"
        "    if retry_budget > 3:\n"
        "        return base + '-retry-%d'\n"
        "    if normalized_state == 'queued' and priority_level > 5:\n"
        "        return base + '-priority-%d'\n"
        "    return base + '-%d'\n"
    ) % (i, i, _normalize_inputs_block(i), i, i, i)


def gen_target_dov(variant, count=20):
    funcs = []
    pick = {"bug": _dov_outcomes_bug, "bugfx": _dov_outcomes_bugfx, "tcc": _dov_outcomes_tcc, "cc": _dov_outcomes_cc}
    for i in range(count):
        funcs.append(pick[variant](i))
    agg = textwrap.dedent(
        '''
        WORKFLOW_STATES = ('ready', 'failed', 'queued', 'cancelled', 'unknown')


        def classify_workflow_state(state):
            normalized = (state or '').strip().lower()
            if normalized in WORKFLOW_STATES:
                return normalized
            return 'unknown'


        def summarize_case_labels(cases):
            labels = []
            for case in cases:
                labels.append(case.get('label', 'case'))
            if not labels:
                return ['empty']
            return labels


        def aggregate_decision_coverage(cases):
            if not cases:
                return 1.0
            covered = sum(1 for c in cases if c.get('covered'))
            return float(covered) / len(cases)
        '''
    )
    lookup = ""
    if variant == "cc":
        lookup = (
            "OUTCOME_LOOKUP = {\n"
            "    ('ready', True): 'started',\n"
            "    ('ready', False): 'disabled',\n"
            "    ('failed', False): 'failed',\n"
            "    ('queued', True): 'queued',\n"
            "}\n\n"
        )
    return _hdr("Decision Outcome Verification", "Coverage.py") + lookup + "\n\n".join(funcs) + "\n\n" + agg


def _epi_payload_block(i):
    return (
        "    if not isinstance(payload, dict):\n"
        "        return 'invalid-%d'\n"
        "    value = payload.get('value', 0)\n"
        "    mode = payload.get('mode', 'fast')\n"
        "    lane = payload.get('lane', 'default')\n"
        "    if value is None:\n"
        "        return 'missing-value-%d'\n"
    ) % (i, i)


def _epi_handler_bugfx(i):
    return (
        "def route_handler_%d(payload):\n"
        '    """Process inbound payload for route %d."""\n'
        "%s"
        "    if value < 0:\n"
        "        return 'negative-%d'\n"
        "    if mode == 'audit':\n"
        "        return 'audit-%d'\n"
        "    if value > 100:\n"
        "        return 'high-%d'\n"
        "    if lane == 'priority':\n"
        "        return 'priority-%d'\n"
        "    return 'ok-%d'\n"
    ) % (i, i, _epi_payload_block(i), i, i, i, i, i)


def _epi_handler_bug(i):
    body = _epi_handler_bugfx(i)
    extra = (
        "    if mode == 'legacy' and value > 50:\n"
        "        return 'legacy-%d'\n"
    ) % i
    return body.replace("    return 'ok-%d'\n" % i, extra + "    return 'ok-%d'\n" % i)


def _epi_handler_tcc(i):
    return (
        "def route_handler_%d(payload):\n"
        '    """Nested branch route handler %d."""\n'
        "    if not isinstance(payload, dict):\n"
        "        return 'invalid-%d'\n"
        "    value = payload.get('value', 0)\n"
        "    mode = payload.get('mode', 'fast')\n"
        "    if value < 0:\n"
        "        return 'negative-%d'\n"
        "    if mode == 'audit':\n"
        "        if value > 50:\n"
        "            return 'audit-strict-%d'\n"
        "        return 'audit-%d'\n"
        "    if value > 100:\n"
        "        return 'high-%d'\n"
        "    return 'ok-%d'\n"
    ) % (i, i, i, i, i, i, i, i)


def _epi_handler_cc(i):
    return (
        "def route_handler_%d(payload):\n"
        '    """Lookup-driven route handler %d."""\n'
        "%s"
        "    label = ROUTE_LABELS.get(mode, 'standard')\n"
        "    if value < 0:\n"
        "        return label + '-negative-%d'\n"
        "    if lane == 'priority':\n"
        "        return label + '-priority-%d'\n"
        "    if value > 100:\n"
        "        return label + '-high-%d'\n"
        "    return label + '-%d'\n"
    ) % (i, i, _epi_payload_block(i), i, i, i, i)


def gen_target_epi(variant, count=26):
    pick = {"bug": _epi_handler_bug, "bugfx": _epi_handler_bugfx, "tcc": _epi_handler_tcc, "cc": _epi_handler_cc}
    funcs = [pick[variant](i) for i in range(count)]
    head = textwrap.dedent(
        '''
        def evaluate_path_integrity(value, mode, flags):
            """Primary execution path integrity evaluator."""
            if not isinstance(flags, dict):
                flags = {}
            if value < 0:
                return 'invalid'
            if mode == 'audit':
                return 'audit-%s' % value
            if mode == 'strict' and value > 75:
                return 'strict-%s' % value
            return 'ok-%s' % value
        '''
    )
    labels = ""
    if variant == "cc":
        labels = "ROUTE_LABELS = {'fast': 'quick', 'audit': 'review', 'strict': 'tight'}\n\n"
    tail = (
        "def summarize_routes(count):\n"
        "    return max(count, 0)\n\n"
    )
    return _hdr("Execution Path Integrity", "Crosshair") + labels + head + "\n\n" + "\n\n".join(funcs) + "\n" + tail


def _lsv_check_bugfx(i):
    return (
        "def condition_check_%d(a, b, c, d, flag):\n"
        '    """Evaluate compound condition set %d."""\n'
        "    active = bool(flag)\n"
        "    left = bool(a and b)\n"
        "    right = bool(c and not d)\n"
        "    if active and (left or right):\n"
        "        return 'accept-%d'\n"
        "    if (a or b) and c:\n"
        "        return 'partial-%d'\n"
        "    if not active and (a or c):\n"
        "        return 'review-%d'\n"
        "    if d and not c:\n"
        "        return 'isolated-%d'\n"
        "    return 'reject-%d'\n"
    ) % (i, i, i, i, i, i, i)


def _lsv_check_bug(i):
    body = _lsv_check_bugfx(i)
    extra = "    if flag and a and c and d:\n        return 'edge-%d'\n" % i
    return body.replace("    return 'reject-%d'\n" % i, extra + "    return 'reject-%d'\n" % i)


def _lsv_check_tcc(i):
    return (
        "def condition_check_%d(a, b, c, d, flag):\n"
        '    """Nested condition check %d."""\n'
        "    if flag:\n"
        "        if a and b:\n"
        "            return 'accept-%d'\n"
        "        if c and not d:\n"
        "            return 'alt-%d'\n"
        "    if (a or b) and c:\n"
        "        return 'partial-%d'\n"
        "    return 'reject-%d'\n"
    ) % (i, i, i, i, i, i)


def _lsv_check_cc(i):
    return (
        "def condition_check_%d(a, b, c, d, flag):\n"
        '    """Score-based condition check %d."""\n'
        "    score = int(bool(a)) + int(bool(b)) + int(bool(c))\n"
        "    active = bool(flag)\n"
        "    if active and score >= 2:\n"
        "        return 'accept-%d'\n"
        "    if score == 1 and active:\n"
        "        return 'neutral-%d'\n"
        "    if not active and score >= 1:\n"
        "        return 'review-%d'\n"
        "    if d and not c:\n"
        "        return 'isolated-%d'\n"
        "    return 'reject-%d'\n"
    ) % (i, i, i, i, i, i, i)


def gen_target_lsv(variant, count=32):
    pick = {"bug": _lsv_check_bug, "bugfx": _lsv_check_bugfx, "tcc": _lsv_check_tcc, "cc": _lsv_check_cc}
    funcs = [pick[variant](i) for i in range(count)]
    helper = textwrap.dedent(
        '''
        def validate_all_conditions(inputs):
            results = []
            for item in inputs:
                results.append(condition_check_0(
                    item.get('a'), item.get('b'), item.get('c'),
                    item.get('d'), item.get('flag')))
            return results
        '''
    )
    tail = textwrap.dedent(
        '''
        CONDITION_LABELS = ('accept', 'partial', 'review', 'reject', 'isolated')


        def label_condition(outcome):
            if not outcome:
                return 'reject'
            for label in CONDITION_LABELS:
                if outcome.startswith(label):
                    return label
            return 'reject'
        '''
    )
    return _hdr("Logical Sub-expression Validation", "Pymcdc") + "\n\n".join(funcs) + "\n\n" + helper + "\n" + tail


def _tlcc_machine_bugfx(i):
    return (
        "def combinatorial_state_machine_%d(bits):\n"
        '    """Walk a compact state machine for pattern %d."""\n'
        "    if not bits:\n"
        "        return 'S0-%d'\n"
        "    state = 'S0'\n"
        "    for idx, bit in enumerate(bits[:8]):\n"
        "        if bit:\n"
        "            state += 'A' + str(idx)\n"
        "        else:\n"
        "            state += 'B' + str(idx)\n"
        "    return state + '-%d'\n"
    ) % (i, i, i, i)


def _tlcc_machine_bug(i):
    body = _tlcc_machine_bugfx(i)
    extra = "    if len(bits) > 20:\n        return 'overflow-%d'\n" % i
    return body.replace("    return state + '-%d'\n" % i, extra + "    return state + '-%d'\n" % i)


def _tlcc_machine_tcc(i):
    return (
        "def combinatorial_state_machine_%d(bits):\n"
        '    """Deeply nested combinatorial walk %d."""\n'
        "    if not bits:\n"
        "        return 'S0-%d'\n"
        "    state = 'S0'\n"
        "    for idx, bit in enumerate(bits[:10]):\n"
        "        if bit:\n"
        "            if idx %% 2 == 0:\n"
        "                state += 'A'\n"
        "            else:\n"
        "                state += 'C'\n"
        "        else:\n"
        "            state += 'B'\n"
        "    return state + '-%d'\n"
    ) % (i, i, i, i)


def _tlcc_machine_cc(i):
    return (
        "def combinatorial_state_machine_%d(bits):\n"
        '    """Parity-based combinatorial summary %d."""\n'
        "    if bits is None:\n"
        "        return 'none-%d'\n"
        "    parity = sum(1 for b in bits if b) %% 2\n"
        "    length = len(bits)\n"
        "    if length == 0:\n"
        "        return 'empty-%d'\n"
        "    if length > 12:\n"
        "        return 'long-%d'\n"
        "    if parity == 1:\n"
        "        return 'odd-' + str(length) + '-%d'\n"
        "    return 'parity-' + str(parity) + '-len-' + str(length) + '-%d'\n"
    ) % (i, i, i, i, i, i, i)


def gen_target_tlcc(variant, count=34):
    pick = {"bug": _tlcc_machine_bug, "bugfx": _tlcc_machine_bugfx, "tcc": _tlcc_machine_tcc, "cc": _tlcc_machine_cc}
    funcs = [pick[variant](i) for i in range(count)]
    helper = (
        "def count_unique_paths(function_name, input_size):\n"
        "    if input_size < 0:\n"
        "        return 0\n"
        "    return 2 ** min(input_size, 10)\n"
    )
    tail = (
        "def summarize_states(states):\n"
        "    return [s for s in states if s]\n\n"
    )
    return _hdr("Total Logical Combinatorial Coverage", "Crosshair") + "\n\n".join(funcs) + "\n\n" + helper + tail


def _tdi_calc_bugfx(i):
    return (
        "def debt_calculator_b%d_v0(amount, rate, years):\n"
        '    """Compound debt projection variant %d."""\n'
        "    if years < 0 or amount < 0:\n"
        "        raise ValueError('invalid input')\n"
        "    principal = float(amount)\n"
        "    annual_rate = float(rate)\n"
        "    if annual_rate < 0:\n"
        "        raise ValueError('invalid rate')\n"
        "    total = principal\n"
        "    for year in range(years):\n"
        "        interest = total * annual_rate\n"
        "        total += interest\n"
        "        if total < 0:\n"
        "            total = 0.0\n"
        "    return round(max(total, 0.0), 2)\n"
    ) % (i, i)


def _tdi_calc_bug(i):
    body = _tdi_calc_bugfx(i)
    extra = "    if years > 30:\n        return -1.0  # defect: invalid sentinel\n"
    return body.replace("    return round(max(total, 0.0), 2)\n", extra + "    return round(max(total, 0.0), 2)\n")


def _tdi_calc_tcc(i):
    return (
        "def debt_calculator_b%d_v0(amount, rate, years):\n"
        '    """Maintainability-friendly debt calculator %d."""\n'
        "    if years < 0 or amount < 0:\n"
        "        raise ValueError('invalid input')\n"
        "    total = float(amount)\n"
        "    for year in range(years):\n"
        "        if year %% 2 == 0:\n"
        "            total += total * rate\n"
        "        else:\n"
        "            total += total * rate * 0.5\n"
        "    return round(max(total, 0.0), 2)\n"
    ) % (i, i)


def _tdi_calc_cc(i):
    return (
        "def debt_calculator_b%d_v0(amount, rate, years):\n"
        '    """Closed-form debt calculator %d."""\n'
        "    if years < 0 or amount < 0:\n"
        "        raise ValueError('invalid input')\n"
        "    principal = float(amount)\n"
        "    annual_rate = float(rate)\n"
        "    if annual_rate < 0:\n"
        "        raise ValueError('invalid rate')\n"
        "    if years == 0:\n"
        "        return round(principal, 2)\n"
        "    multiplier = (1.0 + annual_rate) ** years\n"
        "    total = principal * multiplier\n"
        "    return round(max(total, 0.0), 2)\n"
    ) % (i, i)


def gen_target_tdi(variant, count=36):
    pick = {"bug": _tdi_calc_bug, "bugfx": _tdi_calc_bugfx, "tcc": _tdi_calc_tcc, "cc": _tdi_calc_cc}
    funcs = [pick[variant](i) for i in range(count)]
    tail = textwrap.dedent(
        '''
        def format_debt_total(value):
            return round(float(value), 2)
        '''
    )
    return _hdr("Technical Debt Impact", "Radon/Lizard") + "\n\n".join(funcs) + "\n" + tail


def _qra_bucket_bugfx(i):
    return (
        "def prioritize_test_bucket_%d(modules, history):\n"
        '    """Rank modules into test buckets for cycle %d."""\n'
        "    history = history or {}\n"
        "    ranking = []\n"
        "    for module in modules:\n"
        "        name = module.get('name', 'unknown')\n"
        "        score = module.get('complexity', 0) + history.get(name, 0)\n"
        "        if score > 10:\n"
        "            ranking.append((name, 'high'))\n"
        "        elif score > 5:\n"
        "            ranking.append((name, 'medium'))\n"
        "        else:\n"
        "            ranking.append((name, 'low'))\n"
        "    return ranking\n"
    ) % (i, i)


def _qra_bucket_bug(i):
    body = _qra_bucket_bugfx(i)
    extra = (
        "        if score > 15:\n"
        "            ranking.append((name, 'critical'))\n"
        "            continue\n"
    )
    return body.replace("        if score > 10:\n", extra + "        if score > 10:\n")


def _qra_bucket_tcc(i):
    return (
        "def prioritize_test_bucket_%d(modules, history):\n"
        '    """Nested prioritization ladder %d."""\n'
        "    history = history or {}\n"
        "    ranking = []\n"
        "    for module in modules:\n"
        "        name = module.get('name', 'unknown')\n"
        "        score = module.get('complexity', 0) + history.get(name, 0)\n"
        "        if score > 10:\n"
        "            if history.get(name, 0) > 3:\n"
        "                ranking.append((name, 'high-history'))\n"
        "            else:\n"
        "                ranking.append((name, 'high'))\n"
        "        else:\n"
        "            ranking.append((name, 'low'))\n"
        "    return ranking\n"
    ) % (i, i)


def _qra_bucket_cc(i):
    return (
        "def prioritize_test_bucket_%d(modules, history):\n"
        '    """Simple bucket assignment %d."""\n'
        "    history = history or {}\n"
        "    ranking = []\n"
        "    for module in modules:\n"
        "        name = module.get('name', 'unknown')\n"
        "        score = module.get('complexity', 0) + history.get(name, 0)\n"
        "        if score > 10:\n"
        "            ranking.append((name, 'bucket-high-%d'))\n"
        "        elif score > 5:\n"
        "            ranking.append((name, 'bucket-medium-%d'))\n"
        "        else:\n"
        "            ranking.append((name, 'bucket-low-%d'))\n"
        "    return ranking\n"
    ) % (i, i, i, i, i)


def gen_target_qra(variant, count=40):
    pick = {"bug": _qra_bucket_bug, "bugfx": _qra_bucket_bugfx, "tcc": _qra_bucket_tcc, "cc": _qra_bucket_cc}
    funcs = [pick[variant](i) for i in range(count)]
    tail = textwrap.dedent(
        '''
        def summarize_buckets(ranking):
            return dict(ranking)
        '''
    )
    return _hdr("QA Resource Allocation", "testmon") + "\n\n".join(funcs) + "\n" + tail


TARGET_GENERATORS = {
    "execution_path_integrity": gen_target_epi,
    "decision_coverage": gen_target_dov,
    "condition_coverage": gen_target_lsv,
    "logic_combinatorial": gen_target_tlcc,
    "technical_debt": gen_target_tdi,
    "qa_prioritization": gen_target_qra,
}

VARIANT_MAP = {"Bug": "bug", "BugFX": "bugfx", "TCC": "tcc", "CC": "cc"}


# ---------------------------------------------------------------------------
# main.py — same shape, imports target module for the metric
# ---------------------------------------------------------------------------

def gen_main_py_fixed(abbrev):
    module_key = ABBREV_TO_MODULE[abbrev]
    if abbrev == "DOV":
        return FUTURE + textwrap.dedent(
            '''
            """Demo runner for the target Structural Analysis metric module."""
            from sa.reporting import MetricReportBuilder
            from sa.decision_coverage import decision_case_0, decision_case_1, aggregate_decision_coverage

            SAMPLES = [
                ('ready', True, 0, 1),
                ('failed', False, 0, 1),
                ('queued', True, 0, 9),
                ('ready', True, 5, 2),
            ]

            def evaluate_sample(index, args):
                if index % 2 == 0:
                    return decision_case_0(*args)
                return decision_case_1(*args)

            def main():
                report = MetricReportBuilder('SA DOV demo')
                outcomes = []
                for idx, args in enumerate(SAMPLES):
                    outcome = evaluate_sample(idx, args)
                    outcomes.append(str(outcome))
                    report.add_section('case-%s' % idx, [outcome])
                cov = aggregate_decision_coverage([{'covered': True}, {'covered': False}])
                report.add_section('summary', [
                    'samples=%s' % len(SAMPLES),
                    'coverage=%s' % cov,
                    'first=%s' % (outcomes[0] if outcomes else 'none'),
                ])
                print(report.render_text())

            if __name__ == '__main__':
                main()
            '''
        )
    configs = {
        "EPI": ("execution_path_integrity", "evaluate_path_integrity", "[(5, 'fast', {}), (3, 'audit', {})]"),
        "LSV": ("condition_coverage", "condition_check_0", "[(True, True, False, True, True)]"),
        "TLCC": ("logic_combinatorial", "combinatorial_state_machine_0", "[([True, False, True],)]"),
        "TDI": ("technical_debt", "debt_calculator_b0_v0", "[(100, 0.1, 2)]"),
        "QRA": ("qa_prioritization", "prioritize_test_bucket_0", "[([{'name': 'core', 'complexity': 12}], {})]"),
    }
    mod, fn, samples = configs[abbrev]
    return FUTURE + (
        '"""Demo runner for the target Structural Analysis metric module."""\n'
        "from sa.reporting import MetricReportBuilder\n"
        "from sa.%s import %s\n\n"
        "SAMPLES = %s\n\n"
        "def main():\n"
        "    report = MetricReportBuilder('SA %s demo')\n"
        "    for idx, args in enumerate(SAMPLES):\n"
        "        outcome = %s(*args)\n"
        "        report.add_section('case-%%s' %% idx, [str(outcome)])\n"
        "    report.add_section('summary', ['samples=%%s' %% len(SAMPLES)])\n"
        "    print(report.render_text())\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    ) % (mod, fn, samples, abbrev, fn)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _test_header():
    return FUTURE + "import unittest\n"


def _dov_cases_full():
    lines = ["class TestDecisionCoverage(unittest.TestCase):\n"]
    checks = [
        ("('ready', True, 0, 1)", "started"),
        ("('failed', False, 0, 1)", "failed"),
        ("('ready', False, 0, 1)", "unknown"),
        ("('queued', True, 0, 9)", "priority"),
        ("('ready', True, 5, 1)", "retry"),
        ("('ready', True, 0, 1)", "started"),  # disabled branch for TCC
    ]
    for i in range(n_functions("DOV")):
        for j, (args, prefix) in enumerate(checks):
            lines.append(" def test_case_%d_outcome_%d(self):\n" % (i, j))
            lines.append("  from sa.decision_coverage import decision_case_%d\n" % i)
            lines.append("  self.assertIn('%s', decision_case_%d%s)\n" % (prefix, i, args))
    lines.append(" def test_aggregate_empty(self):\n")
    lines.append("  from sa.decision_coverage import aggregate_decision_coverage\n")
    lines.append("  self.assertEqual(aggregate_decision_coverage([]), 1.0)\n")
    lines.append(" def test_aggregate_partial(self):\n")
    lines.append("  from sa.decision_coverage import aggregate_decision_coverage\n")
    lines.append("  self.assertEqual(aggregate_decision_coverage([{'covered': True}, {'covered': False}]), 0.5)\n")
    return _test_header() + "".join(lines)


def _dov_cases_bug():
    return _test_header() + textwrap.dedent(
        '''
        from sa.decision_coverage import decision_case_0

        class TestDecisionCoverageBug(unittest.TestCase):
            def test_started_only(self):
                self.assertIn('started', decision_case_0('ready', True, 0, 1))
        '''
    )


def _stub_sanity_tests(abbrev):
    """A few sanity tests on non-target stub modules."""
    stubs = {
        "DOV": [
            ("test_execution_path_integrity_stub", "sa.execution_path_integrity", "evaluate_path_integrity", "1, 'fast', {}"),
            ("test_data_repository_stub", "sa.data_repository", "MetricDataRepository", ""),
        ],
        "EPI": [
            ("test_decision_coverage_stub", "sa.decision_coverage", "aggregate_decision_coverage", "[]"),
            ("test_data_repository_stub", "sa.data_repository", "MetricDataRepository", ""),
        ],
    }
    default = [
        ("test_data_repository_stub", "sa.data_repository", "MetricDataRepository", ""),
        ("test_reporting_stub", "sa.reporting", "MetricReportBuilder", "'title'"),
    ]
    cases = stubs.get(abbrev, default)
    lines = [_test_header(), "class TestStubSanity(unittest.TestCase):\n"]
    for method, mod, sym, args in cases:
        lines.append(" def %s(self):\n" % method)
        if args:
            lines.append("  from %s import %s\n" % (mod, sym))
            lines.append("  self.assertTrue(%s(%s) is not None)\n" % (sym, args))
        else:
            lines.append("  from %s import %s\n" % (mod, sym))
            lines.append("  self.assertTrue(%s() is not None)\n" % sym)
    return "".join(lines)


def _gen_tests_generic(abbrev, branch_type, files):
    """Generate tests for EPI, LSV, TLCC, TDI, QRA."""
    cfg = {
        "EPI": ("execution_path_integrity", "evaluate_path_integrity", "(5, 'fast', {})", "audit"),
        "LSV": ("condition_coverage", "condition_check_0", "(True, True, False, True, True)", "accept"),
        "TLCC": ("logic_combinatorial", "combinatorial_state_machine_0", "([True, False],)", "S0"),
        "TDI": ("technical_debt", "debt_calculator_b0_v0", "(100, 0.1, 2)", ""),
        "QRA": ("qa_prioritization", "prioritize_test_bucket_0", "([{'name': 'a', 'complexity': 1}], {})", "low"),
    }
    mod, fn, args, expect = cfg[abbrev]
    if branch_type == "Bug":
        if abbrev in ("EPI", "TDI"):
            return files
        files["tests/test_%s.py" % mod] = _test_header() + textwrap.dedent(
            '''
            from sa.%s import %s

            class TestBugPartial(unittest.TestCase):
                def test_partial_only(self):
                    self.assertTrue(%s%s)
            '''
        ) % (mod, fn, fn, args)
        return files
    lines = [_test_header(), "class Test%sFull(unittest.TestCase):\n" % abbrev]
    for i in range(n_functions(abbrev)):
        fn_i = fn.replace("_0", "_%d" % i) if "_0" in fn else fn.replace("b0", "b%d" % i)
        if abbrev == "EPI":
            fn_i = "route_handler_%d" % i
            call = "({'value': 1, 'mode': 'fast'},)"
        elif abbrev == "LSV":
            fn_i = "condition_check_%d" % i
            call = "(True, True, False, True, True)"
        elif abbrev == "TLCC":
            fn_i = "combinatorial_state_machine_%d" % i
            call = "([True, False],)"
        elif abbrev == "TDI":
            fn_i = "debt_calculator_b%d_v0" % i
            call = "(100, 0.1, 2)"
        elif abbrev == "QRA":
            fn_i = "prioritize_test_bucket_%d" % i
            call = "([{'name': 'a', 'complexity': 1}], {})"
        else:
            call = args
        lines.append(" def test_%s_%d(self):\n" % (mod, i))
        lines.append("  from sa.%s import %s\n" % (mod, fn_i))
        lines.append("  self.assertTrue(%s%s)\n" % (fn_i, call))
    files["tests/test_%s.py" % mod] = "".join(lines)
    if branch_type in ("BugFX", "TCC", "CC"):
        files["tests/test_stub_sanity.py"] = _stub_sanity_tests(abbrev)
    return files


# Patch gen_tests to handle all abbrevs
def gen_tests(abbrev, branch_type):
    files = {"tests/__init__.py": FUTURE}
    if abbrev == "DOV":
        if branch_type == "Bug":
            files["tests/test_decision_coverage.py"] = _dov_cases_bug()
        else:
            files["tests/test_decision_coverage.py"] = _dov_cases_full()
            files["tests/test_stub_sanity.py"] = _stub_sanity_tests(abbrev)
        return files
    return _gen_tests_generic(abbrev, branch_type, files)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def gen_readme(branch_name, abbrev, branch_type):
    meta = METRIC_META[ABBREV_TO_MODULE[abbrev]]
    table = "\n".join(
        "| %s | %s | %s | %s |" % (METRIC_META[mk][0], METRIC_META[mk][3], METRIC_META[mk][1], METRIC_META[mk][2])
        for mk in MODULE_KEYS
    )
    return (
        "# %s\n\nPython 2.6 Structural Analysis — metric-scoped **%s** branch.\n\n"
        "- Target: %s (%s)\n- Classification: %s\n\n%s\n"
    ) % (branch_name, branch_type, meta[1], abbrev, meta[3], table)


def gen_requirements(branch_type):
    if branch_type == "TCC":
        return "# TCC tooling\ncoverage==3.7.1\nradon==1.4.2\npytest==2.6.4\ntestmon==0.4.5\n"
    return "# Tests\npytest==2.6.4\n"


def gen_tool_configs(branch_type):
    if branch_type != "TCC":
        return {}
    return {
        ".coveragerc": "[run]\nbranch = True\nsource = sa\nomit = tests/*\n",
        "setup.cfg": "[radon]\ncc_min = A\n",
        "pytest.ini": "[pytest]\ntestpaths = tests\n",
        ".testmondata.ini": "[testmon]\ndepth = module\n",
    }


def count_loc(files, prefixes=("sa/", "tests/", "main.py")):
    total = 0
    for path, content in files.items():
        if not any(path.startswith(p) or path == p.strip("/") for p in prefixes):
            continue
        if path == "main.py" or path.startswith("sa/") or path.startswith("tests/"):
            total += content.count("\n") + (0 if content.endswith("\n") else 1)
    return total


def generate_branch_files(abbrev, branch_type, version="2.6", language="python"):
    variant = VARIANT_MAP[branch_type]
    target_module = ABBREV_TO_MODULE[abbrev]
    branch_name = "SA_%s_%s_%s" % (abbrev, branch_type, version)

    files = {}
    files["sa/config.py"] = gen_config_py(abbrev, branch_type, version, language)
    for rel, gen_fn in SUPPORT_GENERATORS.items():
        files[rel] = gen_fn()

    for mk in MODULE_KEYS:
        rel = "sa/%s.py" % mk
        if mk == target_module:
            files[rel] = TARGET_GENERATORS[mk](variant, n_functions(abbrev))
        else:
            files[rel] = _stub_metric_module(mk)

    files["main.py"] = gen_main_py_fixed(abbrev)
    files["README.md"] = gen_readme(branch_name, abbrev, branch_type)
    files["requirements.txt"] = gen_requirements(branch_type)
    files["versions.txt"] = "SA_%s_*_%s\n" % (abbrev, version)
    files.update(gen_tool_configs(branch_type))
    files.update(gen_tests(abbrev, branch_type))

    for path, content in files.items():
        if path.endswith(".py"):
            _assert_no_forbidden(content, path)

    loc = count_loc(files)
    if loc < MIN_LOC:
        raise ValueError("Generated %s has only %d LOC (need >= %d)" % (branch_name, loc, MIN_LOC))
    return files


def write_branch(root, abbrev, branch_type, version="2.6", language="python"):
    import shutil
    files = generate_branch_files(abbrev, branch_type, version, language)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    for rel, content in files.items():
        path = os.path.join(root, rel)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    loc = count_loc(files)
    bname = "SA_%s_%s_%s" % (abbrev, branch_type, version)
    return bname, loc


def generate_all_branches(metrics="all", version="2.6", language="python", build_dir="build", repo_root=None):
    """Generate all metric branches under build_dir. Returns list of branch names."""
    from lib.sa_metrics import FIXED_BRANCH_TYPES, branch_name, parse_metrics_arg

    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    names = []
    for abbrev in parse_metrics_arg(metrics):
        for bt in FIXED_BRANCH_TYPES:
            bname = branch_name(abbrev, bt, version)
            out_path = os.path.join(root, build_dir, bname)
            write_branch(out_path, abbrev, bt, version, language)
            names.append(bname)
    return names


_GIT_KEEP = {".git", "build", "lib", "notebooks", "tools", "archive", "runs", ".gitignore", ".env.local"}


def _git_run(cmd, cwd):
    import subprocess
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def _clean_worktree(repo_root):
    import shutil
    for name in os.listdir(repo_root):
        if name in _GIT_KEEP:
            continue
        path = os.path.join(repo_root, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def _deploy_branch(repo_root, branch, build_dir="build"):
    import shutil
    _clean_worktree(repo_root)
    src = os.path.join(repo_root, build_dir, branch)
    if not os.path.isdir(src):
        raise RuntimeError("Missing build output: %s" % src)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(repo_root, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    add_paths = ["sa", "tests", "README.md", "main.py", "requirements.txt", "versions.txt"]
    for optional in (".coveragerc", ".testmondata.ini", "pytest.ini", "setup.cfg"):
        if os.path.exists(os.path.join(repo_root, optional)):
            add_paths.append(optional)
    _git_run(["git", "add", "-A"] + add_paths, repo_root)
    _git_run(["git", "commit", "-m", "Add metric-scoped SA %s codebase" % branch], repo_root)


def create_git_branches(metrics="all", version="2.6", language="python", repo_root=None, build_dir="build"):
    """Create git branches from validated build/ output."""
    from lib.sa_metrics import FIXED_BRANCH_TYPES, branch_name, parse_metrics_arg

    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    branches = []
    for abbrev in parse_metrics_arg(metrics):
        for bt in FIXED_BRANCH_TYPES:
            branches.append(branch_name(abbrev, bt, version))
    for branch in branches:
        _git_run(["git", "checkout", "-B", branch, "main"], root)
        _deploy_branch(root, branch, build_dir)
    _git_run(["git", "checkout", "main"], root)
    return branches


def push_branches(branch_names, repo_root=None):
    import subprocess
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    git_env = dict(os.environ)
    git_env.update({
        "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never",
        "GIT_ASKPASS": "echo", "SSH_ASKPASS": "echo",
    })
    for name in branch_names:
        subprocess.check_call(
            ["git", "-c", "credential.helper=", "push", "-u", "origin", name, "--force"],
            cwd=root, env=git_env,
        )
