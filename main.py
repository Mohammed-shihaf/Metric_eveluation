from __future__ import print_function
"""Demo runner for the target Structural Analysis metric module."""
from sa.reporting import MetricReportBuilder
from sa.logic_combinatorial import combinatorial_state_machine_0

SAMPLES = [([True, False, True],)]

def main():
    report = MetricReportBuilder('SA TLCC demo')
    for idx, args in enumerate(SAMPLES):
        outcome = combinatorial_state_machine_0(*args)
        report.add_section('case-%s' % idx, [str(outcome)])
    report.add_section('summary', ['samples=%s' % len(SAMPLES)])
    print(report.render_text())

if __name__ == '__main__':
    main()
