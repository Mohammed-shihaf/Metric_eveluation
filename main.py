from __future__ import print_function
"""Demo runner for the target Structural Analysis metric module."""
from sa.reporting import MetricReportBuilder
from sa.execution_path_integrity import evaluate_path_integrity

SAMPLES = [(5, 'fast', {}), (3, 'audit', {})]

def main():
    report = MetricReportBuilder('SA EPI demo')
    for idx, args in enumerate(SAMPLES):
        outcome = evaluate_path_integrity(*args)
        report.add_section('case-%s' % idx, [str(outcome)])
    report.add_section('summary', ['samples=%s' % len(SAMPLES)])
    print(report.render_text())

if __name__ == '__main__':
    main()
