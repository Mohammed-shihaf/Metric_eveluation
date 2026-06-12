from __future__ import print_function
"""Demo runner for the target Structural Analysis metric module."""
from sa.reporting import MetricReportBuilder
from sa.technical_debt import debt_calculator_b0_v0

SAMPLES = [(100, 0.1, 2)]

def main():
    report = MetricReportBuilder('SA TDI demo')
    for idx, args in enumerate(SAMPLES):
        outcome = debt_calculator_b0_v0(*args)
        report.add_section('case-%s' % idx, [str(outcome)])
    report.add_section('summary', ['samples=%s' % len(SAMPLES)])
    print(report.render_text())

if __name__ == '__main__':
    main()
