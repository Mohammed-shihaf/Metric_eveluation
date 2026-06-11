from __future__ import print_function

from sa.config import BRANCH_VARIANT, TESTING_TYPE, PYTHON_VERSION, METRIC_TOOL_MAP
from sa.models import RepositorySnapshot, WorkflowContext
from sa.data_repository import AnalysisRepository
from sa.workflow_orchestrator import StructuralAnalysisWorkflow
from sa.reporting import format_metric_row, render_text_report

def build_snapshot():
    snapshot = RepositorySnapshot('sa-python26', loc=12000, language_version=PYTHON_VERSION)
    for module_name in METRIC_TOOL_MAP.keys():
        snapshot.register_module(module_name, complexity=22)
    return snapshot

def main():
    print('Branch:', BRANCH_VARIANT, 'Python:', PYTHON_VERSION, 'Type:', TESTING_TYPE)
    workflow = StructuralAnalysisWorkflow(AnalysisRepository())
    snapshot = build_snapshot()
    context = WorkflowContext('wf-001', 'qa-analyst')
    results = workflow.run_all(snapshot)
    rows = [format_metric_row(v['metric'], v['classification'], v['tool'], 75, 'pending')
            for v in METRIC_TOOL_MAP.values()]
    print(render_text_report(rows))
    print('Results:', len(results), 'Errors:', len(context.errors))

if __name__ == '__main__':
    main()
