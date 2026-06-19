"""Run registry primary tools locally and emit standard tool reports."""

from __future__ import print_function

import contextlib
import json
import os
import shutil
import subprocess
import sys

from lib.github_api import materialize_branch
from lib.lang_support import branch_language, branch_language_by_name, normalize_language
from lib.registry import iter_branches
from lib.report_schema import from_tool_assert_result, save_report
from lib.tool_map import metric_tool, pip_packages_for_family, pip_packages_for_primary, all_tool_packages
from lib.tool_assert import _branch_context

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _pipeline_work_branch_paths(repo_root, bname):
    """Find branch copies under any .pipeline_work/<user_key>/ folder."""
    base = os.path.join(repo_root, ".pipeline_work")
    if not os.path.isdir(base):
        return []
    paths = []
    for key in sorted(os.listdir(base)):
        path = os.path.join(base, key, bname)
        if os.path.isdir(path):
            paths.append(path)
    return paths


def _local_branch_candidates(repo_root, build_dir, bname, local_root=None):
    """Return ordered candidate paths for a branch (local copies first)."""
    candidates = []
    if local_root:
        candidates.append(os.path.join(local_root, bname))
    for path in _pipeline_work_branch_paths(repo_root, bname):
        if path not in candidates:
            candidates.append(path)
    candidates.append(os.path.join(repo_root, build_dir, bname))
    if build_dir and build_dir != "build":
        candidates.append(os.path.join(repo_root, "build", bname))
    return candidates


def _pick_branch_path(repo_root, build_dir, bname, local_root=None):
    for path in _local_branch_candidates(repo_root, build_dir, bname, local_root=local_root):
        if os.path.isdir(path):
            return path
    return None


@contextlib.contextmanager
def _resolve_branch_path(
    repo_root,
    build_dir,
    bname,
    github_config=None,
    ref=None,
    local_root=None,
):
    local_path = _pick_branch_path(repo_root, build_dir, bname, local_root=local_root)
    if local_path:
        yield local_path
        return
    if github_config and github_config.get("token") and github_config.get("repo_slug"):
        with materialize_branch(
            github_config["token"],
            github_config["repo_slug"],
            bname,
            ref=ref or bname,
        ) as path:
            yield path
        return
    fallback = os.path.join(repo_root, build_dir, bname)
    if not os.path.isdir(fallback):
        raise FileNotFoundError(
            "branch not found locally or on GitHub: %s (checked %s)"
            % (bname, ", ".join(_local_branch_candidates(repo_root, build_dir, bname, local_root=local_root)))
        )
    yield fallback


REPORT_START = "<<<REPORT>>>"
REPORT_END = "<<<END>>>"


def _persistent_env_enabled():
    return os.environ.get("LOCAL_TOOL_PERSISTENT", "true").lower() in ("1", "true", "yes")


def _family_install_blockers(technique_code, metric_code, language, install_result):
    """Return list of failed packages required by this branch's family."""
    info = metric_tool(technique_code, metric_code, language)
    needed = pip_packages_for_primary(
        info.get("primary", ""),
        info.get("family", ""),
        technique_code,
    )
    failed = set(install_result.get("failed") or [])
    return [p for p in needed if p in failed]


def _attach_diagnostics(report, assert_result=None, install_result=None, doctor_matrix=None, worker_log=""):
    extra = dict(report.get("extra") or {})
    if assert_result:
        log = assert_result.get("log") or ""
        if log:
            extra["tool_log"] = log
            extra["tool_stderr"] = log
        msg = assert_result.get("message") or ""
        if msg and assert_result.get("status") in ("UNAVAILABLE", "SKIPPED"):
            extra["tool_unavailable"] = msg
            extra["tool_stderr"] = extra.get("tool_stderr") or msg
    if install_result:
        extra["install_failed"] = install_result.get("failed", [])
        extra["install_installed"] = install_result.get("installed", []) + install_result.get("skipped", [])
        if install_result.get("failed"):
            extra["install_error"] = install_result.get("message", "")
    if doctor_matrix:
        extra["doctor"] = {
            "env_key": doctor_matrix.get("env_key", ""),
            "all_runnable": doctor_matrix.get("all_runnable"),
            "families": doctor_matrix.get("families", {}),
        }
    if worker_log:
        extra["worker_log"] = _sanitize_worker_log(worker_log)
    report["extra"] = extra
    return report


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


def ensure_tool_installed(technique_code, metric_code, language="python", branch_path=None):
    """Install packages required for the metric's registry primary tool."""
    lang = normalize_language(language or "python")
    from lib.tool_map import metric_tool

    info = metric_tool(technique_code, metric_code, lang)
    if lang != "python":
        from lib.lang_tool_runners import packages_for_language, toolchain_available

        pkgs = packages_for_language(info["family"], info["primary"], lang)
        ok, detail = toolchain_available(lang)
        if not ok:
            return False, detail
        if lang in ("javascript", "typescript") and pkgs and shutil.which("npm"):
            cwd = branch_path if branch_path and os.path.isdir(branch_path) else None
            cmd = ["npm", "install", "--no-save", "--silent"] + pkgs
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
                if proc.returncode != 0:
                    return False, (proc.stderr or proc.stdout or "npm install failed").strip()
                return True, "installed npm: %s" % ", ".join(pkgs)
            except (OSError, subprocess.TimeoutExpired) as exc:
                return False, str(exc)
        if lang in ("java", "csharp"):
            return True, "%s toolchain ready (%s)" % (lang, info.get("primary", ""))
        return True, "structural %s validation" % lang

    packages = pip_packages_for_primary(
        info.get("primary", ""),
        info.get("family", ""),
        technique_code,
    )
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
    require_real_tool=False,
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

    lang = normalize_language(language or branch_language(branch_path))

    if install:
        ok, msg = ensure_tool_installed(technique_code, metric_code, lang, branch_path=branch_path)
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

    tool_info = metric_tool(technique_code, metric_code, lang)
    registry_primary = (tool_info.get("primary") or "").strip()

    assert_result = tool_assert_branch(
        branch_path,
        technique_code,
        metric_code,
        branch_type,
        lang,
        require_real_tool=require_real_tool,
    )
    report = from_tool_assert_result(
        assert_result,
        source="local",
        commit_sha=commit_sha,
        run_id=run_id,
        version=version,
        language=lang,
    )
    extra = dict(report.get("extra") or {})
    executed = assert_result.get("tool_used", "")
    real_tool = assert_result.get("real_tool")
    if real_tool is None:
        real_tool = not str(executed).startswith("structural")
    if registry_primary:
        report["tool_name"] = registry_primary
        extra["registry_primary"] = registry_primary
        extra["executed_tool"] = executed
    extra["real_tool"] = bool(real_tool)
    if not real_tool and require_real_tool:
        report["status"] = assert_result.get("status", "UNAVAILABLE")
        extra["tool_unavailable"] = assert_result.get("message", "real tool did not execute")
    for key in (
        "actual_outcome",
        "expected_outcome",
        "strength_pass",
        "strength_score",
        "strength_reason",
        "raw_metric_value",
        "metric_value",
        "tool_outcome",
        "config_effective",
        "expected_threshold",
    ):
        if key in assert_result:
            val = assert_result.get(key)
            if val is not None and val != "":
                extra[key] = val
            elif isinstance(val, bool):
                extra[key] = val
    if assert_result.get("status") in ("PASS", "FAIL"):
        extra["assert_status"] = assert_result.get("status")
    if install_msg:
        extra["install_msg"] = install_msg
    log = assert_result.get("log") or ""
    if log:
        extra["tool_log"] = log
        extra["tool_stderr"] = log
    if assert_result.get("status") in ("UNAVAILABLE",) and assert_result.get("message"):
        extra["tool_stderr"] = assert_result.get("message")
    report["extra"] = extra
    return report


def required_packages_for_branches(branch_names, language=None, language_by_branch=None, repo_root=None, local_root=None):
    """Union of pip packages for each branch's registry primary tool (Python branches only)."""
    from lib.metrics import parse_branch_name
    from lib.lang_tool_runners import packages_for_language

    repo_root = repo_root or ROOT
    if language_by_branch is None:
        language_by_branch = branch_language_by_name(
            branch_names, repo_root, local_root=local_root, fallback=language or "python",
        )
    packages = []
    for bname in branch_names:
        parsed = parse_branch_name(bname)
        if not parsed:
            continue
        lang = normalize_language(language_by_branch.get(bname) or language or "python")
        info = metric_tool(parsed["tech"], parsed["metric"], lang)
        if lang != "python":
            continue
        pkgs = pip_packages_for_primary(
            info.get("primary", ""),
            info.get("family", ""),
            parsed["tech"],
        )
        packages.extend(pkgs)
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


def _run_worker_for_branch(
    session,
    repo_root,
    branch_path,
    tech,
    metric,
    bt,
    version,
    commit_sha,
    run_id,
    language="python",
    require_real_tool=True,
):
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
        "--language",
        normalize_language(language or branch_language(branch_path)),
    ]
    if require_real_tool:
        cmd.append("--require-real-tool")
    if commit_sha:
        cmd.extend(["--commit-sha", commit_sha])
    if run_id:
        cmd.extend(["--run-id", run_id])
    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=3600,
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


def _sanitize_worker_log(text):
    """Remove worker report JSON sentinels; keep stderr/stdout tool output only."""
    text = text or ""
    if REPORT_START in text and REPORT_END in text:
        before = text.split(REPORT_START, 1)[0]
        after = text.split(REPORT_END, 1)[-1]
        text = (before + after).strip()
    return _truncate_log(text)


def run_local_tool_batch_isolated(
    branches,
    build_dir="build",
    output_dir="proofs",
    root=None,
    commit_sha_by_branch=None,
    run_id_by_branch=None,
    progress_callback=None,
    github_config=None,
    local_root=None,
    language=None,
    language_by_branch=None,
):
    """Run local tools in a persistent or throwaway venv; only reports persist on disk."""
    from lib.metrics import infer_from_branch_name, parse_branch_name
    from lib.report_schema import make_report
    from lib.tool_doctor import run_tool_doctor
    from lib.tool_env import ensure_tool_env
    from lib.tool_session import create_session, destroy_session, install_packages

    repo_root = root or ROOT
    commit_sha_by_branch = commit_sha_by_branch or {}
    run_id_by_branch = run_id_by_branch or {}
    if language_by_branch is None:
        language_by_branch = branch_language_by_name(
            branches, repo_root, local_root=local_root, fallback=language or "python",
        )
    total = len(branches)
    reports = []
    session = None
    install_result = {"ok": True, "message": "", "failed": [], "installed": [], "skipped": [], "logs": []}
    doctor_matrix = None
    persistent = _persistent_env_enabled()

    try:
        packages = list(dict.fromkeys(
            required_packages_for_branches(
                branches,
                language=language,
                language_by_branch=language_by_branch,
                repo_root=repo_root,
                local_root=local_root,
            ) + all_tool_packages()
        ))
        has_python = any(
            normalize_language(language_by_branch.get(b, language or "python")) == "python"
            for b in branches
        )
        if not has_python:
            packages = []

        if progress_callback:
            progress_callback(
                "session",
                0,
                total,
                "",
                "preparing tool environment (%s)" % ("persistent" if persistent else "throwaway"),
            )

        if persistent:
            if packages:
                session = ensure_tool_env(packages)
            else:
                session = {"python_exe": sys.executable, "env": os.environ.copy(), "install_result": install_result}
            install_result = session.get("install_result") or install_result
            if packages:
                if progress_callback:
                    progress_callback("session", 0, total, "", "running tool doctor preflight")
                doctor_matrix = run_tool_doctor(packages=packages, persist=True)
                if doctor_matrix.get("session"):
                    doctor_matrix.pop("session", None)
        else:
            if packages:
                session = create_session()
                install_result = install_packages(session, packages)
            else:
                session = {"python_exe": sys.executable, "env": os.environ.copy()}
                install_result = {"ok": True, "message": "native toolchain batch", "failed": [], "installed": [], "skipped": [], "logs": []}

        install_msg = install_result.get("message", "")
        if not install_result.get("ok", False):
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
                    extra={
                        "install_error": install_msg,
                        "install_msg": install_msg,
                        "install_failed": install_result.get("failed", []),
                        "session": "persistent" if persistent else "isolated",
                    },
                )
                report = _attach_diagnostics(report, install_result=install_result, doctor_matrix=doctor_matrix)
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
                    extra={"session": "persistent" if persistent else "isolated"},
                )
            else:
                branch_lang = normalize_language(language_by_branch.get(bname, language or "python"))
                blockers = _family_install_blockers(tech, metric, branch_lang, install_result)
                if blockers:
                    report = make_report(
                        technique_code=tech,
                        metric_code=metric,
                        branch_name=bname,
                        branch_type=bt,
                        version=version,
                        tool_name="",
                        source="local",
                        status="ERROR",
                        raw_summary="required packages failed to install: %s" % ", ".join(blockers),
                        commit_sha=commit_sha_by_branch.get(bname, ""),
                        run_id=run_id_by_branch.get(bname, ""),
                        extra={
                            "install_failed": blockers,
                            "install_msg": install_msg,
                            "session": "persistent" if persistent else "isolated",
                        },
                    )
                    report = _attach_diagnostics(report, install_result=install_result, doctor_matrix=doctor_matrix)
                else:
                    ref = commit_sha_by_branch.get(bname, "") or bname
                    try:
                        with _resolve_branch_path(
                            repo_root,
                            build_dir,
                            bname,
                            github_config=github_config,
                            ref=ref,
                            local_root=local_root,
                        ) as branch_path:
                            if branch_lang in ("javascript", "typescript"):
                                ensure_tool_installed(tech, metric, branch_lang, branch_path=branch_path)
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
                                language=branch_lang,
                                require_real_tool=True,
                            )
                        extra = dict(report.get("extra") or {})
                        extra["install_msg"] = install_msg
                        extra["session"] = "persistent" if persistent else "isolated"
                        tool_log = extra.get("tool_log") or ""
                        if worker_log and not tool_log:
                            extra["tool_log"] = _sanitize_worker_log(worker_log)
                            extra["tool_stderr"] = extra["tool_log"]
                        elif worker_log:
                            extra["worker_log"] = _sanitize_worker_log(worker_log)
                        report["extra"] = extra
                        report = _attach_diagnostics(
                            report,
                            install_result=install_result,
                            doctor_matrix=doctor_matrix,
                            worker_log=worker_log,
                        )
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
                            extra={
                                "install_msg": install_msg,
                                "session": "persistent" if persistent else "isolated",
                                "error": str(exc),
                                "tool_stderr": str(exc),
                            },
                        )
                        report = _attach_diagnostics(
                            report,
                            install_result=install_result,
                            doctor_matrix=doctor_matrix,
                        )
            out_path = os.path.join(repo_root, output_dir, tech or "?", bname, "local_report.json")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            extra = dict(report.get("extra") or {})
            extra["report_path"] = out_path
            report["extra"] = extra
            save_report(report, out_path)
            report["_path"] = out_path
            reports.append(report)
            if progress_callback:
                progress_callback("local", idx, total, bname, report.get("status", "OK"))
    finally:
        if progress_callback:
            progress_callback("session", total, total, "", "session ready" if persistent else "removing session")
        if not persistent:
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
