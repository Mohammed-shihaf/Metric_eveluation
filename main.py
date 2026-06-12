from __future__ import print_function
"""Demo runner for the target Structural Analysis metric module."""
from sa.reporting import MetricReportBuilder
from sa.condition_coverage import condition_check_0

SAMPLES = [(True, True, False, True, True)]

def main():
    report = MetricReportBuilder('SA LSV demo')
    for idx, args in enumerate(SAMPLES):
        outcome = condition_check_0(*args)
        report.add_section('case-%s' % idx, [str(outcome)])
    report.add_section('summary', ['samples=%s' % len(SAMPLES)])
    print(report.render_text())

if __name__ == '__main__':
    main()
