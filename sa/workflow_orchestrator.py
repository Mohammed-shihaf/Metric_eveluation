from __future__ import print_function

from sa.execution_path_integrity import METRIC_NAME as EPI_METRIC
from sa.decision_coverage import METRIC_NAME as DC_METRIC
from sa.condition_coverage import METRIC_NAME as CC_METRIC
from sa.logic_combinatorial import METRIC_NAME as LC_METRIC
from sa.technical_debt import METRIC_NAME as TD_METRIC
from sa.qa_prioritization import METRIC_NAME as QA_METRIC

class StructuralAnalysisWorkflow(object):
    def __init__(self, repository):
        self.repository = repository
    def run_all(self, snapshot):
        return [
            {'metric': EPI_METRIC, 'modules': len(snapshot.modules)},
            {'metric': DC_METRIC, 'modules': len(snapshot.modules)},
            {'metric': CC_METRIC, 'modules': len(snapshot.modules)},
            {'metric': LC_METRIC, 'modules': len(snapshot.modules)},
            {'metric': TD_METRIC, 'total_cc': snapshot.total_complexity()},
            {'metric': QA_METRIC, 'module_count': len(snapshot.modules)},
        ]
