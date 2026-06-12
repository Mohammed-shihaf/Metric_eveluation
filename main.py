from __future__ import print_function
"""Demo runner for the target Structural Analysis metric module."""
from sa.reporting import MetricReportBuilder
from sa.qa_prioritization import prioritize_test_bucket_0

SAMPLES = [([{'name': 'core', 'complexity': 12}], {})]

def main():
    report = MetricReportBuilder('SA QRA demo')
    for idx, args in enumerate(SAMPLES):
        outcome = prioritize_test_bucket_0(*args)
        report.add_section('case-%s' % idx, [str(outcome)])
    report.add_section('summary', ['samples=%s' % len(SAMPLES)])
    print(report.render_text())

if __name__ == '__main__':
    main()
