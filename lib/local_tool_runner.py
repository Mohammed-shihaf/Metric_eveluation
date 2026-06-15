"""Run registry primary tools locally and emit standard tool reports."""

from __future__ import print_function

import contextlib
import json
import os
import subprocess
import sys

from lib.github_api import materialize_branch
from lib.registry import iter_branches
from lib.report_schema import from_tool_assert_result, save_report
from lib.tool_map import pip_packages_for_family, python_tool
from lib.tool_assert import _branch_context

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@contextlib.contextmanager
def _resolve_branch_path(repo_root, build_dir, bname, github_config=None, ref=None):
    if github_config and github_config.get("token") and github_config.get("repo_slug"):
        with materialize_branch(
            github_config["token"],
            github_config["repo_slug"],
            bname,
            ref=ref or bname,
        ) as path:
            yield path
    else:
        yield os.path.join(repo_root, build_dir, bname)

REPORT_START = "<<<REPORT>>>"
REPORT_END = "<<<END>>>"


def _python_module_available(module):
    try:
        proc = subprocess.run(
            [sys.executable, "-c", "import %s" % module.replace("-", "_")],
            capture_output=True,
            timeout=15,
            check=False,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _pytest_ready():
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            timeout=20,
            check=False,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def ensure_tool_installed(technique_code, metric_code, language="python"):
    """Install pip packages required for the metric's primary tool family."""
    if language != "python":
        return False, "only python supported"
    info = python_tool(technique_code, metric_code)
    packages = pip_packages_for_family(info["family"], info["primary"])
    if not packages:
        return True, "no pip packages required for family %s" % info["family"]

    missing = []
    for pkg in packages:
        mod = pkg.replace("-", "_")
        if pkg == "pip-audit":
            mod = "pip_audit"
        if not _python_module_available(mod):
            missing.append(pkg)

    if "pytest" in packages and not _pytest_ready():
        missing.append("pytest>=7.0.0")

    if not missing:
        return True, "tools available"

    cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + missing
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "pip install failed").strip()
        return True, "installed: %s" % ", ".join(missing)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)


def run_local_tool_report(
    branch_path,
    technique_code=None,
    metric_code=None,
    branch_type=None,
    version=None,
    language="python",
    commit_sha=None,
    run_id=None,
    install=True,
):
    """Execute local tool for one branch and return a standard report dict."""
    from lib.tool_assert import tool_assert_branch

    folder = os.path.basename(os.path.normpath(branch_path))
    from lib.metrics import parse_branch_name

    parsed = parse_branch_name(folder)
    if not parsed:
        raise ValueError("unparseable branch folder: %s" % folder)

    technique_code = (technique_code or parsed["tech"]).upper()
    metric_code = (metric_code or parsed["metric"]).upper()
    branch_type = branch_type or parsed["type"]
    version = version or parsed["version"]

    if install:
        ok, msg = ensure_tool_installed(technique_code, metric_code, language)
        install_msg = msg
        if not ok:
            from lib.report_schema import make_report

            return make_report(
                technique_code=technique_code,
                metric_code=metric_code,
                branch_name=folder,
                branch_type=branch_type,
                version=version,
                tool_name="",
                source="local",
                status="ERROR",
                raw_summary=msg,
                commit_sha=commit_sha,
                run_id=run_id,
                extra={"install_error": msg, "install_msg": msg},
            )
    else:
        install_msg = ""

    assert_result = tool_assert_branch(
        branch_path, technique_code, metric_code, branch_type, language
    )
    report = from_tool_assert_result(
        assert_result,
        source="local",
        commit_sha=commit_sha,
        run_id=run_id,
        version=version,
    )
    extra = dict(report.get("extra") or {})
    if install_msg:
        extra["install_msg"] = install_msg
    if extra:
        report["extra"] = extra
    return report


def required_packages_for_branches(branch_names, language="python"):
    """Union of pip packages needed for a set of branch folder names."""
    if language != "python":
        return []
    from lib.metrics import parse_branch_name

    packages = []
    for bname in branch_names:
        parsed = parse_branch_name(bname)
        if not parsed:
            continue
        info = python_tool(parsed["tech"], parsed["metric"])
        packages.extend(pip_packages_for_family(info["family"], info["primary"]))
    return list(dict.fromkeys(packages))


def _parse_worker_report(stdout):
    """Extract JSON report between sentinel markers."""
    text = stdout or ""
    if REPORT_START in text and REPORT_END in text:
        chunk = text.split(REPORT_START, 1)[1].split(REPORT_END, 1)[0].strip()
        return json.loads(chunk)
    # fallback: last JSON object in output
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    raise ValueError("worker did not return a report")


def _run_worker_for_branch(session, repo_root, branch_path, tech, metric, bt, version, commit_sha, run_id):
    """Launch venv worker subprocess; return (report_dict, worker_log)."""
    cmd = [
        session["python_exe"],
        "-m",
        "lib.local_tool_worker",
        "--branch-path",
        branch_path,
        "--technique",
        tech,
        "--metric",
        metric,
        "--type",
        bt,
        "--version",
        version,
    ]
    if commit_sha:
        cmd.extend(["--commit-sha", commit_sha])
    if run_id:
        cmd.extend(["--run-id", run_id])
    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
        env=session.get("env"),
    )
    log = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(
            "worker exit %d: %s" % (proc.returncode, _truncate_log(log, 2000))
        )
    return _parse_worker_report(proc.stdout), log


def _truncate_log(text, max_len=4000):
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated)"


def run_local_tool_batch_isolated(
    branches,
    build_dir="build",
    output_dir="proofs",
    root=None,
    commit_sha_by_branch=None,
    run_id_by_branch=None,
    progress_callback=None,
    github_config=None,
):
    """Run local tools in a throwaway venv; only reports persist on disk."""
    from lib.metrics import infer_from_branch_name, parse_branch_name
    from lib.report_schema import make_report
    from lib.tool_session import create_session, destroy_session, install_packages

    repo_root = root or ROOT
    commit_sha_by_branch = commit_sha_by_branch or {}
    run_id_by_branch = run_id_by_branch or {}
    total = len(branches)
    reports = []
    session = None
    install_msg = ""

    try:
        if progress_callback:
            progress_callback("session", 0, total, "", "creating isolated session")
        session = create_session()
        packages = required_packages_for_branches(branches)
        if progress_callback:
            progress_callback("session", 0, total, "", "installing tools in session")
        ok, install_msg = install_packages(session, packages)
        if not ok:
            for bname in branches:
                parsed = parse_branch_name(bname)
                tech = parsed["tech"] if parsed else ""
                metric = parsed["metric"] if parsed else ""
                bt = parsed["type"] if parsed else ""
                ver = parsed["version"] if parsed else "2.6"
                report = make_report(
                    technique_code=tech,
                    metric_code=metric,
                    branch_name=bname,
                    branch_type=bt,
                    version=ver,
                    tool_name="",
                    source="local",
                    status="ERROR",
                    raw_summary=install_msg,
                    extra={"install_error": install_msg, "install_msg": install_msg, "session": "isolated"},
                )
                out_path = os.path.join(repo_root, output_dir, tech, bname, "local_report.json")
                save_report(report, out_path)
                report["_path"] = out_path
                reports.append(report)
            return reports

        for idx, bname in enumerate(branches, start=1):
            if progress_callback:
                progress_callback("local", idx - 1, total, bname, "running in session")
            tech, metric, bt, version = infer_from_branch_name(bname)
            if not tech:
                report = make_report(
                    technique_code="",
                    metric_code="",
                    branch_name=bname,
                    branch_type="",
                    version="2.6",
                    tool_name="",
                    source="local",
                    status="ERROR",
                    raw_summary="unparseable branch name",
                    extra={"session": "isolated"},
                )
            else:
                ref = commit_sha_by_branch.get(bname, "") or bname
                try:
                    with _resolve_branch_path(
                        repo_root, build_dir, bname, github_config=github_config, ref=ref,
                    ) as branch_path:
                        report, worker_log = _run_worker_for_branch(
                            session,
                            repo_root,
                            branch_path,
                            tech,
                            metric,
                            bt,
                            version,
                            commit_sha_by_branch.get(bname, ""),
                            run_id_by_branch.get(bname, ""),
                        )
                    extra = dict(report.get("extra") or {})
                    extra["install_msg"] = install_msg
                    extra["session"] = "isolated"
                    if worker_log:
                        extra["tool_log"] = _truncate_log(worker_log)
                    report["extra"] = extra
                except Exception as exc:
                    report = make_report(
                        technique_code=tech,
                        metric_code=metric,
                        branch_name=bname,
                        branch_type=bt,
                        version=version,
                        tool_name="",
                        source="local",
                        status="ERROR",
                        raw_summary=str(exc),
                        commit_sha=commit_sha_by_branch.get(bname, ""),
                        run_id=run_id_by_branch.get(bname, ""),
                        extra={"install_msg": install_msg, "session": "isolated", "error": str(exc)},
                    )
            out_path = os.path.join(repo_root, output_dir, tech or "?", bname, "local_report.json")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            save_report(report, out_path)
            report["_path"] = out_path
            reports.append(report)
            if progress_callback:
                progress_callback("local", idx, total, bname, report.get("status", "OK"))
    finally:
        if progress_callback:
            progress_callback("session", total, total, "", "removing session")
        destroy_session(session)

    return reports


def run_local_tool_batch(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    language="python",
    build_dir="build",
    output_dir="proofs",
    root=None,
    install=True,
    commit_sha_by_branch=None,
    run_id_by_branch=None,
):
    """Run local tools for selected branches; write standard reports under proofs/."""
    repo_root = root or ROOT
    commit_sha_by_branch = commit_sha_by_branch or {}
    run_id_by_branch = run_id_by_branch or {}
    reports = []

    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        branch_path = os.path.join(repo_root, build_dir, bname)
        report = run_local_tool_report(
            branch_path,
            tech,
            metric,
            bt,
            version,
            language,
            commit_sha=commit_sha_by_branch.get(bname, ""),
            run_id=run_id_by_branch.get(bname, ""),
            install=install,
        )
        out_path = os.path.join(
            repo_root, output_dir, tech, bname, "local_report.json"
        )
        save_report(report, out_path)
        report["_path"] = out_path
        reports.append(report)

    return reports


def default_report_path(root, technique_code, branch_name, source="local"):
    filename = "%s_report.json" % source
    return os.path.join(root, "proofs", technique_code, branch_name, filename)
