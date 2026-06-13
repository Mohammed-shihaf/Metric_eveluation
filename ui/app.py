"""Metric Evaluation pipeline UI — end-to-end with strong triggers."""

from __future__ import print_function

import json
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.branch_asserts import assert_build_batch  # noqa: E402
from lib.compare import compare_report_files, summarize_comparisons  # noqa: E402
from lib.credentials import audit_credentials  # noqa: E402
from lib.generator import create_git_branches, generate_branches, push_branches  # noqa: E402
from lib.metrics import github_branch_url, scan_build_dir  # noqa: E402
from lib.pipeline_selection import (  # noqa: E402
    branch_type_options,
    csv_from_list,
    metric_options,
    selection_summary,
    technique_options,
)
from lib.proofs import collect_comparison_proof, collect_proofs_batch, list_proof_branches, load_proof_bundle  # noqa: E402
from lib.registry import load_registry  # noqa: E402
from lib.sa_qa import run_taxonomy_batch, verify_taxonomy_dir  # noqa: E402
from lib.s3_sync import sync_from_taxonomy_meta  # noqa: E402
from lib.taxonomy_meta import latest_taxonomy_by_branch, parse_taxonomy_html  # noqa: E402
from lib.ui_run_panel import RunPanel  # noqa: E402

st.set_page_config(page_title="Metric Evaluation Pipeline", layout="wide", initial_sidebar_state="expanded")
st.title("Metric Evaluation Pipeline")
st.caption("Generate → assert → GitHub · Whitebox + S3 · Local tools · Compare")


def _readiness():
    audit = audit_credentials(str(ROOT / ".env.local"), root=str(ROOT))
    return audit


def _sidebar_filters():
    st.sidebar.header("Selection")
    registry = load_registry()
    tech_opts = technique_options(registry)
    tech_codes = [c for c, _ in tech_opts]

    use_all = st.sidebar.checkbox("All techniques (412)", value=False)
    if use_all:
        techniques, selected_techniques = "all", tech_codes
    else:
        selected_techniques = st.sidebar.multiselect(
            "Techniques", tech_codes, default=["SA"],
            format_func=lambda c: next(l for code, l in tech_opts if code == c),
        )
        techniques = csv_from_list(selected_techniques) if selected_techniques else "SA"

    use_all_metrics = st.sidebar.checkbox("All metrics", value=False)
    if use_all_metrics:
        metrics = "all"
    else:
        metric_choices = []
        for tc in (selected_techniques if not use_all else ["SA"]):
            for m in metric_options(tc, registry):
                metric_choices.append("%s:%s" % (tc, m))
        picked = st.sidebar.multiselect("Metrics", sorted(set(metric_choices)))
        if picked and len({p.split(":")[0] for p in picked}) == 1:
            metrics = csv_from_list([p.split(":")[1] for p in picked])
        else:
            metrics = "DOV" if techniques == "SA" else "all"

    type_opts = branch_type_options(registry)
    types = st.sidebar.multiselect("Branch types", type_opts, default=type_opts) or type_opts
    version = st.sidebar.text_input("Version", "2.6")

    summary = selection_summary(techniques, metrics, types, version, registry)
    st.sidebar.metric("In scope", summary["branch_count"])

    audit = _readiness()
    c1, c2 = st.sidebar.columns(2)
    c1.metric("QA", "OK" if audit["testable_ready"] else "—")
    c2.metric("S3", "OK" if audit["s3_ready"] else "—")

    return {
        "techniques": techniques,
        "metrics": metrics,
        "types": types,
        "version": version,
        "language": "python",
        "summary": summary,
        "env_file": str(ROOT / ".env.local"),
        "audit": audit,
    }


def _tab_branches(filters):
    st.header("1 — Generate branches")
    total = filters["summary"]["branch_count"]

    on_disk = scan_build_dir("build", str(ROOT))
    matched = [r for r in on_disk if r.get("metric") != "?"]
    st.metric("Branches on disk (build/)", len(matched))
    if matched:
        display_cols = ["branch_name", "technique", "metric", "branch_type", "version"]
        st.dataframe(
            [{k: r.get(k, "") for k in display_cols} for r in matched[:100]],
            use_container_width=True,
        )

    col1, col2, col3 = st.columns(3)
    do_assert = col1.checkbox("Run assert validation", value=True)
    do_git = col2.checkbox("Create git branches", value=False)
    do_push = col3.checkbox("Push to GitHub", value=False, disabled=not do_git)
    push_only_pass = st.checkbox("Push only branches that pass asserts", value=True)

    if st.button("Generate branches", type="primary", use_container_width=True):
        with RunPanel("Generating %d branches" % total) as panel:
            names, errors = generate_branches(
                filters["techniques"], filters["metrics"], filters["types"],
                filters["version"], filters["language"], "build", str(ROOT),
                continue_on_error=False,
                progress_callback=panel.progress,
            )
            if errors:
                st.error(errors[0]["error"])
                st.stop()
            st.session_state["last_generated"] = names
            panel.progress("generate", len(names), total, "", "generated %d" % len(names))

            assert_rows = []
            if do_assert:
                with panel.stdout_redirect():
                    assert_rows = assert_build_batch(
                        filters["techniques"], filters["metrics"], filters["types"],
                        filters["version"], filters["language"], "build", str(ROOT),
                        progress_callback=panel.progress,
                    )
                st.session_state["last_asserts"] = assert_rows
                st.dataframe(assert_rows, use_container_width=True)

            if do_git:
                panel.progress("git", 0, total, "", "creating git branches (isolated worktree)")
                to_push = names
                if push_only_pass and assert_rows:
                    passed = {r["branch_name"] for r in assert_rows if r["overall"] == "PASS"}
                    to_push = [n for n in names if n in passed]
                with panel.stdout_redirect():
                    created, git_errors = create_git_branches(
                        filters["techniques"], filters["metrics"], filters["types"],
                        filters["version"], filters["language"], str(ROOT), "build",
                        progress_callback=panel.progress,
                    )
                if git_errors:
                    st.warning("Git branch issues: %d (e.g. %s)" % (len(git_errors), git_errors[0]["error"]))
                if do_push and to_push:
                    panel.progress("git", 0, len(to_push), "", "pushing to origin")
                    with panel.stdout_redirect():
                        push_branches(to_push, str(ROOT))
                    st.session_state["last_pushed"] = to_push
                    repo = os.environ.get("REPOSITORY_MATCH", "")
                    for b in to_push[:10]:
                        st.markdown("- [%s](%s)" % (b, github_branch_url(b, repo)))
        st.toast("Branch generation finished", icon="✅")

    if st.session_state.get("last_asserts"):
        st.subheader("Last assert results")
        st.dataframe(st.session_state["last_asserts"], use_container_width=True)


def _tab_whitebox(filters):
    st.header("2 — Whitebox QA + taxonomy + S3")
    if not filters["audit"]["testable_ready"]:
        st.warning("QA credentials not ready in .env.local")

    branches_csv = ",".join(filters["summary"]["branches"])
    st.code(branches_csv, language=None)

    if st.button("Run whitebox batch", type="primary", use_container_width=True):
        with RunPanel("Whitebox QA") as panel:
            with panel.stdout_redirect():
                rc, batch_dir = run_taxonomy_batch(
                    env_file=filters["env_file"],
                    branches_csv=branches_csv,
                    dry_run=False,
                    refresh_branches=True,
                    allow_partial_branches=True,
                    export_html=True,
                    html_only=False,
                    progress_callback=panel.progress,
                )
            st.session_state["last_qa_rc"] = rc
            st.session_state["last_qa_batch"] = batch_dir
            if rc == 0 and batch_dir:
                failed = verify_taxonomy_dir(str(batch_dir))
                st.info("Taxonomy verify failures: %d" % failed)
                panel.progress("s3", 0, len(filters["summary"]["branches"]), "", "syncing S3")
                s3_rows = []
                group = Path(batch_dir).parent.name
                class_dir = Path(batch_dir).parent
                for idx, bname in enumerate(filters["summary"]["branches"], 1):
                    meta = latest_taxonomy_by_branch(class_dir).get(bname, {})
                    if meta:
                        with panel.stdout_redirect():
                            row = sync_from_taxonomy_meta(meta)
                        s3_rows.append(row)
                    panel.progress("s3", idx, len(filters["summary"]["branches"]), bname, "synced")
                st.session_state["last_s3_sync"] = s3_rows
                st.dataframe(
                    [{"branch": r.get("branch"), "status": r.get("status"), "files": r.get("files_downloaded")} for r in s3_rows],
                    use_container_width=True,
                )
        st.toast("Whitebox batch finished", icon="✅")


def _tab_local_s3(filters):
    st.header("3 — Collect proofs (local + S3)")
    if st.button("Collect proofs", type="primary", use_container_width=True):
        with RunPanel("Proof collection") as panel:
            with panel.stdout_redirect():
                results = collect_proofs_batch(
                    techniques=filters["techniques"],
                    metrics=filters["metrics"],
                    types=filters["types"],
                    version=filters["version"],
                    build_dir="build",
                    root=str(ROOT),
                    install_local=True,
                    sync_s3=True,
                    run_local=True,
                    compare=False,
                    progress_callback=panel.progress,
                )
            st.session_state["last_proof_collection"] = results
            st.dataframe(
                [{
                    "branch": r["branch_name"],
                    "status": r.get("status"),
                    "s3": (r.get("s3_report") or {}).get("status"),
                    "local": (r.get("local_report") or {}).get("status"),
                } for r in results],
                use_container_width=True,
            )
        st.toast("Proofs collected", icon="✅")


def _tab_comparison(filters):
    st.header("4 — Compare taxonomy / S3 / local")
    if st.button("Run comparison", type="primary", use_container_width=True):
        with RunPanel("Comparison") as panel:
            results = []
            branches = filters["summary"]["branches"]
            for idx, bname in enumerate(branches, 1):
                panel.progress("compare", idx - 1, len(branches), bname, "")
                try:
                    results.append(collect_comparison_proof(bname, root=str(ROOT)))
                except Exception as exc:
                    results.append({"branch_name": bname, "verdict": "ERROR", "summary": str(exc)})
                panel.progress("compare", idx, len(branches), bname, results[-1].get("verdict", ""))
            st.session_state["last_comparisons"] = results
            summary = summarize_comparisons(results)
            st.success("MATCH=%d MISMATCH=%d INCOMPLETE=%d" % (
                summary["match"], summary["mismatch"], summary["incomplete"]))
        st.toast("Comparison done", icon="✅")

    proof_rows = list_proof_branches(str(ROOT))
    if proof_rows:
        st.dataframe(proof_rows, use_container_width=True)

    picks = filters["summary"]["branches"]
    if picks:
        branch_pick = st.selectbox("Inspect branch", picks)
        bundle = load_proof_bundle(branch_pick, root=str(ROOT))
        if bundle:
            t1, t2, t3, t4 = st.tabs(["Taxonomy", "S3", "Local", "Comparison"])
            with t1:
                st.json(bundle.get("taxonomy_report") or {})
            with t2:
                st.json(bundle.get("s3_report") or {})
            with t3:
                st.json(bundle.get("local_report") or {})
            with t4:
                st.json(bundle.get("comparison") or {})


def main():
    filters = _sidebar_filters()
    t1, t2, t3, t4 = st.tabs(["Branches", "Whitebox", "Proofs", "Compare"])
    with t1:
        _tab_branches(filters)
    with t2:
        _tab_whitebox(filters)
    with t3:
        _tab_local_s3(filters)
    with t4:
        _tab_comparison(filters)


if __name__ == "__main__":
    main()
