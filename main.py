from __future__ import print_function

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
