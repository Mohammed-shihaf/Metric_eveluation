"""Backward-compatible shim — use lib.metrics for registry-driven naming."""

from lib.metrics import *  # noqa: F401,F403

from lib.metrics import get_sa_metrics

SA_METRICS = get_sa_metrics()
METRIC_ABBREVS = [r[1] for r in SA_METRICS]
ABBREV_TO_MODULE = {r[1]: r[0] for r in SA_METRICS}
ABBREV_TO_CLASSIFICATION = {r[1]: r[2] for r in SA_METRICS}
MODULE_TO_ABBREV = {r[0]: r[1] for r in SA_METRICS}
SA_TESTING_TYPE = "Structural Analysis"


def branch_name(abbrev, branch_type="Bug", version="2.6"):
    from lib.metrics import branch_name as bn
    return bn("SA", abbrev, branch_type, version)


from lib.metrics import (  # noqa: E402
    branch_name_from_report_folder,
    infer_metric_from_report_folder,
    report_folder_name,
    report_output_dir,
)
