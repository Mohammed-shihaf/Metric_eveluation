"""SonarQube Community runner — Docker-managed server + scanner per branch."""

from __future__ import print_function

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

from lib.report_schema import _status_from_metric_values, make_report
from lib.tool_assert import _pytest_ready, _python_module_available, _run

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_HOST = "http://localhost:9000"
DEFAULT_CONTAINER = "tas-sonarqube"
DEFAULT_SERVER_IMAGE = "sonarqube:community"
DEFAULT_SCANNER_IMAGE = "sonarsource/sonar-scanner-cli"
DEFAULT_ADMIN_LOGIN = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"
LOCAL_ADMIN_PASSWORD = "TasSonarLocal1!"
TOKEN_FILE = ".sonar_token"
ADMIN_PWD_FILE = ".sonar_admin_pwd"

SONAR_METRICS = (
    "coverage,bugs,vulnerabilities,code_smells,duplicated_lines_density,"
    "complexity,cognitive_complexity,ncloc,sqale_index,reliability_rating,"
    "security_rating,sqale_rating"
)

SERVER_START_TIMEOUT_SEC = 180
CE_POLL_TIMEOUT_SEC = 300
CE_POLL_INTERVAL_SEC = 3
DOCKER_CHECK_TIMEOUT_SEC = 45
DOCKER_CMD_TIMEOUT_SEC = 120


def _env(key, default=""):
    return str(os.environ.get(key, default)).strip() or default


def sonar_config():
    return {
        "host_url": _env("SONAR_HOST_URL", DEFAULT_HOST).rstrip("/"),
        "container_name": _env("SONAR_CONTAINER_NAME", DEFAULT_CONTAINER),
        "server_image": _env("SONAR_DOCKER_IMAGE", DEFAULT_SERVER_IMAGE),
        "scanner_image": _env("SONAR_SCANNER_IMAGE", DEFAULT_SCANNER_IMAGE),
    }


def _repo_paths(root=None):
    repo = Path(root or ROOT)
    return {
        "repo": repo,
        "token": repo / TOKEN_FILE,
        "admin_pwd": repo / ADMIN_PWD_FILE,
    }


def _docker_available():
    last_err = ""
    for attempt in range(2):
        try:
            proc = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=DOCKER_CHECK_TIMEOUT_SEC,
                check=False,
            )
            if proc.returncode == 0 and (proc.stdout or "").strip():
                return True, (proc.stdout or "").strip()
            last_err = (proc.stderr or proc.stdout or "docker info failed").strip()
            if "error during connect" in last_err.lower() or "cannot connect" in last_err.lower():
                last_err = "Docker daemon not running — start Docker Desktop and retry"
            elif "500 Internal Server Error" in last_err:
                last_err = "Docker API error — restart Docker Desktop and retry"
            if attempt == 0:
                time.sleep(2)
        except subprocess.TimeoutExpired:
            last_err = (
                "Docker did not respond within %ds — ensure Docker Desktop is running"
                % DOCKER_CHECK_TIMEOUT_SEC
            )
            break
        except OSError as exc:
            last_err = str(exc)
            break
    return False, last_err


def _docker_run(args, timeout=DOCKER_CMD_TIMEOUT_SEC):
    try:
        proc = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, "", str(exc)


def _container_state(name):
    rc, out, _ = _docker_run(
        ["ps", "-a", "--filter", "name=^/%s$" % name, "--format", "{{.State}}"]
    )
    if rc != 0:
        return "unknown"
    return (out or "").strip().lower() or "missing"


def _wait_sonar_up(host_url, timeout_sec=SERVER_START_TIMEOUT_SEC):
    deadline = time.time() + timeout_sec
    last = ""
    while time.time() < deadline:
        try:
            resp = requests.get("%s/api/system/status" % host_url, timeout=10)
            if resp.status_code == 200:
                status = resp.json().get("status", "")
                last = status
                if status == "UP":
                    return True, "UP"
        except requests.RequestException as exc:
            last = str(exc)
        time.sleep(3)
    return False, last or "timeout"


def _read_cached_token(root=None):
    path = _repo_paths(root)["token"]
    if path.is_file():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    return ""


def _write_cached_token(token, root=None):
    path = _repo_paths(root)["token"]
    path.write_text(token.strip(), encoding="utf-8")


def _read_admin_password(root=None):
    path = _repo_paths(root)["admin_pwd"]
    if path.is_file():
        pwd = path.read_text(encoding="utf-8").strip()
        if pwd:
            return pwd
    return LOCAL_ADMIN_PASSWORD


def _write_admin_password(password, root=None):
    path = _repo_paths(root)["admin_pwd"]
    path.write_text(password.strip(), encoding="utf-8")


def _basic_auth(login, password):
    return (login, password)


def _api_get(host_url, path, auth=None, token=None, timeout=30):
    headers = {}
    auth_tuple = auth
    if token:
        headers["Authorization"] = "Bearer %s" % token
        auth_tuple = None
    return requests.get(
        "%s%s" % (host_url, path),
        auth=auth_tuple,
        headers=headers,
        timeout=timeout,
    )


def _api_post(host_url, path, data=None, auth=None, token=None, timeout=30):
    headers = {}
    auth_tuple = auth
    if token:
        headers["Authorization"] = "Bearer %s" % token
        auth_tuple = None
    return requests.post(
        "%s%s" % (host_url, path),
        data=data or {},
        auth=auth_tuple,
        headers=headers,
        timeout=timeout,
    )


def _ensure_admin_password(host_url, root=None):
    """Set admin password on first boot (default admin/admin) and return working creds."""
    login = DEFAULT_ADMIN_LOGIN
    stored = _read_admin_password(root)

    resp = _api_post(
        host_url,
        "/api/authentication/validate",
        auth=_basic_auth(login, stored),
    )
    if resp.status_code == 200 and resp.json().get("valid"):
        return login, stored

    resp = _api_post(
        host_url,
        "/api/authentication/validate",
        auth=_basic_auth(login, DEFAULT_ADMIN_PASSWORD),
    )
    if resp.status_code == 200 and resp.json().get("valid"):
        change = _api_post(
            host_url,
            "/api/users/change_password",
            data={
                "login": login,
                "previousPassword": DEFAULT_ADMIN_PASSWORD,
                "password": stored,
            },
            auth=_basic_auth(login, DEFAULT_ADMIN_PASSWORD),
        )
        if change.status_code not in (200, 204):
            return None, None
        _write_admin_password(stored, root)
        return login, stored

    return None, None


def ensure_sonar_token(host_url=None, root=None):
    """Return a SonarQube user token (cached on disk)."""
    cfg = sonar_config()
    host_url = (host_url or cfg["host_url"]).rstrip("/")
    cached = _read_cached_token(root)
    if cached:
        probe = _api_get(host_url, "/api/authentication/validate", token=cached)
        if probe.status_code == 200 and probe.json().get("valid"):
            return cached

    login, password = _ensure_admin_password(host_url, root)
    if not login:
        raise RuntimeError("cannot authenticate SonarQube admin user")

    resp = _api_post(
        host_url,
        "/api/user_tokens/generate",
        data={"name": "tas-pipeline", "login": login},
        auth=_basic_auth(login, password),
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            "token generation failed (%s): %s" % (resp.status_code, resp.text[:300])
        )
    token = resp.json().get("token", "")
    if not token:
        raise RuntimeError("token generation returned empty token")
    _write_cached_token(token, root)
    return token


def ensure_sonar_server(root=None):
    """Start or verify the SonarQube Docker container. Returns (ok, host_url, message)."""
    cfg = sonar_config()
    host_url = cfg["host_url"]
    name = cfg["container_name"]
    image = cfg["server_image"]

    ok, msg = _docker_available()
    if not ok:
        return False, host_url, "Docker not available: %s" % msg

    state = _container_state(name)
    if state == "missing":
        rc, out, err = _docker_run(
            [
                "run", "-d",
                "--name", name,
                "-p", "9000:9000",
                image,
            ],
            timeout=120,
        )
        if rc != 0:
            return False, host_url, "docker run failed: %s" % (err or out)
        state = "created"
    elif state in ("exited", "dead", "created"):
        rc, out, err = _docker_run(["start", name], timeout=60)
        if rc != 0:
            return False, host_url, "docker start failed: %s" % (err or out)

    up, detail = _wait_sonar_up(host_url)
    if not up:
        return False, host_url, "SonarQube not UP within timeout (last: %s)" % detail
    return True, host_url, "SonarQube running at %s (container %s)" % (host_url, name)


def sonar_server_status(root=None):
    """Lightweight status probe without starting the server."""
    cfg = sonar_config()
    host_url = cfg["host_url"]
    docker_ok, docker_msg = _docker_available()
    state = "n/a"
    if docker_ok:
        state = _container_state(cfg["container_name"])
    try:
        resp = requests.get("%s/api/system/status" % host_url, timeout=5)
        sq_status = resp.json().get("status", "?") if resp.status_code == 200 else "DOWN"
    except requests.RequestException:
        sq_status = "DOWN"
    return {
        "docker_ok": docker_ok,
        "docker_msg": docker_msg,
        "container_state": state,
        "host_url": host_url,
        "system_status": sq_status,
        "ready": docker_ok and sq_status == "UP",
    }


def _sanitize_project_key(branch_name):
    key = re.sub(r"[^A-Za-z0-9._:\-]", "_", branch_name)
    return key[:400]


def _generate_coverage_xml(branch_path):
    """Run pytest under coverage and emit coverage.xml for Sonar."""
    branch_path = Path(branch_path)
    log_lines = []
    if not _python_module_available("coverage"):
        return False, "coverage.py not installed", "\n".join(log_lines)

    if not _pytest_ready():
        return False, "pytest not available", "\n".join(log_lines)

    for cmd in (
        [sys.executable, "-m", "coverage", "erase"],
        [sys.executable, "-m", "coverage", "run", "--branch", "-m", "pytest", "tests/", "-q", "--tb=no"],
        [sys.executable, "-m", "coverage", "xml", "-o", "coverage.xml"],
    ):
        rc, out, err = _run(cmd, str(branch_path), timeout=120)
        log_lines.append("$ %s" % " ".join(cmd))
        if out:
            log_lines.append(out.rstrip())
        if err:
            log_lines.append(err.rstrip())
        if rc != 0 and "coverage xml" in " ".join(cmd):
            return False, "coverage xml failed (rc=%d)" % rc, "\n".join(log_lines)

    cov_xml = branch_path / "coverage.xml"
    if not cov_xml.is_file():
        return False, "coverage.xml not produced", "\n".join(log_lines)
    return True, "coverage.xml ready", "\n".join(log_lines)


def _scanner_host_url(host_url):
    """URL reachable from inside the scanner container."""
    if "localhost" in host_url or "127.0.0.1" in host_url:
        return host_url.replace("localhost", "host.docker.internal").replace(
            "127.0.0.1", "host.docker.internal"
        )
    return host_url


def _parse_ce_task_id(branch_path):
    report_task = Path(branch_path) / ".scannerwork" / "report-task.txt"
    if not report_task.is_file():
        return ""
    for line in report_task.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("ceTaskId="):
            return line.split("=", 1)[1].strip()
    return ""


def _poll_ce_task(host_url, task_id, token, timeout_sec=CE_POLL_TIMEOUT_SEC):
    deadline = time.time() + timeout_sec
    last = {}
    while time.time() < deadline:
        resp = _api_get(host_url, "/api/ce/task?id=%s" % task_id, token=token)
        if resp.status_code == 200:
            last = resp.json().get("task", {})
            status = last.get("status", "")
            if status == "SUCCESS":
                return True, last
            if status in ("FAILED", "CANCELED"):
                return False, last
        time.sleep(CE_POLL_INTERVAL_SEC)
    return False, last


def _fetch_measures(host_url, project_key, token):
    resp = requests.get(
        "%s/api/measures/component" % host_url,
        params={"component": project_key, "metricKeys": SONAR_METRICS},
        headers={"Authorization": "Bearer %s" % token},
        timeout=30,
    )
    if resp.status_code != 200:
        return {}, "measures API failed (%s): %s" % (resp.status_code, resp.text[:200])
    measures = {}
    for item in resp.json().get("component", {}).get("measures", []):
        metric = item.get("metric", "")
        value = item.get("value", "")
        if metric and value is not None:
            try:
                measures[metric] = float(value) if "." in str(value) else int(value)
            except (TypeError, ValueError):
                measures[metric] = value
    return measures, ""


def _measures_to_metric_values(measures):
    values = {}
    if "coverage" in measures:
        values["coverage_pct"] = float(measures["coverage"])
    if "duplicated_lines_density" in measures:
        values["dup_pct"] = float(measures["duplicated_lines_density"])
    if "vulnerabilities" in measures:
        values["vulns"] = int(measures["vulnerabilities"])
    if "code_smells" in measures:
        values["issues"] = int(measures["code_smells"])
    if "bugs" in measures:
        values["bugs"] = int(measures["bugs"])
    if "complexity" in measures:
        values["complexity"] = int(measures["complexity"])
    if "cognitive_complexity" in measures:
        values["cognitive_complexity"] = int(measures["cognitive_complexity"])
    if "ncloc" in measures:
        values["ncloc"] = int(measures["ncloc"])
    return values


def sonar_report_from_measures(
    measures,
    technique_code,
    metric_code,
    branch_name,
    branch_type,
    version,
    commit_sha="",
    run_id="",
    log="",
    project_key="",
):
    from lib.report_schema import _tool_family_for_metric

    metric_values = _measures_to_metric_values(measures)
    family = _tool_family_for_metric(technique_code, metric_code)
    if metric_values and family:
        status = _status_from_metric_values(family, metric_values, branch_type)
    elif measures:
        status = "WARN"
    else:
        status = "ERROR"

    parts = []
    if "coverage" in measures:
        parts.append("%.1f%% cov" % float(measures["coverage"]))
    if "bugs" in measures:
        parts.append("bugs=%s" % measures["bugs"])
    if "vulnerabilities" in measures:
        parts.append("vulns=%s" % measures["vulnerabilities"])
    if "code_smells" in measures:
        parts.append("smells=%s" % measures["code_smells"])

    extra = {
        "sonar_project_key": project_key or _sanitize_project_key(branch_name),
        "sonar_measures": measures,
        "tool_family": family or "sonar",
    }
    if log:
        extra["tool_log"] = log[:4000] if len(log) > 4000 else log

    return make_report(
        technique_code=technique_code,
        metric_code=metric_code,
        branch_name=branch_name,
        branch_type=branch_type,
        version=version,
        tool_name="SonarQube Community",
        source="sonar",
        status=status,
        metric_values=metric_values,
        raw_summary=" ".join(parts) or "sonar scan complete",
        commit_sha=commit_sha,
        run_id=run_id,
        extra=extra,
    )


def run_sonar_for_branch(branch_path, project_key=None, host_url=None, token=None, root=None):
    """Scan one branch directory; return (report_dict, log_text)."""
    cfg = sonar_config()
    host_url = (host_url or cfg["host_url"]).rstrip("/")
    branch_path = Path(branch_path).resolve()
    if not branch_path.is_dir():
        raise ValueError("branch path missing: %s" % branch_path)

    folder = branch_path.name
    from lib.metrics import infer_from_branch_name

    tech, metric, branch_type, version = infer_from_branch_name(folder)
    if not tech:
        raise ValueError("unparseable branch folder: %s" % folder)

    project_key = project_key or _sanitize_project_key(folder)
    token = token or ensure_sonar_token(host_url, root=root)
    scanner_host = _scanner_host_url(host_url)

    log_parts = []
    ok, cov_msg, cov_log = _generate_coverage_xml(branch_path)
    log_parts.append(cov_log)
    if not ok:
        report = make_report(
            technique_code=tech,
            metric_code=metric,
            branch_name=folder,
            branch_type=branch_type,
            version=version,
            tool_name="SonarQube Community",
            source="sonar",
            status="SKIPPED",
            raw_summary=cov_msg,
            extra={"skip_reason": cov_msg, "tool_log": cov_log},
        )
        return report, "\n".join(log_parts)

    branch_mount = str(branch_path)
    if os.name == "nt":
        branch_mount = branch_mount.replace("\\", "/")

    from lib.registry import package_name

    sources_dir = package_name(tech)
    scanner_cmd = [
        "run", "--rm",
        "-v", "%s:/usr/src" % branch_mount,
        cfg["scanner_image"],
        "-Dsonar.projectKey=%s" % project_key,
        "-Dsonar.projectName=%s" % folder,
        "-Dsonar.sources=%s" % sources_dir,
        "-Dsonar.python.version=3",
        "-Dsonar.host.url=%s" % scanner_host,
        "-Dsonar.token=%s" % token,
        "-Dsonar.python.coverage.reportPaths=coverage.xml",
    ]
    rc, out, err = _docker_run(scanner_cmd, timeout=600)
    log_parts.append("$ docker %s" % " ".join(scanner_cmd))
    if out:
        log_parts.append(out.rstrip())
    if err:
        log_parts.append(err.rstrip())

    if rc != 0:
        report = make_report(
            technique_code=tech,
            metric_code=metric,
            branch_name=folder,
            branch_type=branch_type,
            version=version,
            tool_name="SonarQube Community",
            source="sonar",
            status="ERROR",
            raw_summary="sonar-scanner failed (rc=%d)" % rc,
            extra={"tool_log": "\n".join(log_parts)[-4000:]},
        )
        return report, "\n".join(log_parts)

    task_id = _parse_ce_task_id(branch_path)
    if not task_id:
        report = make_report(
            technique_code=tech,
            metric_code=metric,
            branch_name=folder,
            branch_type=branch_type,
            version=version,
            tool_name="SonarQube Community",
            source="sonar",
            status="ERROR",
            raw_summary="no ceTaskId in report-task.txt",
            extra={"tool_log": "\n".join(log_parts)[-4000:]},
        )
        return report, "\n".join(log_parts)

    ce_ok, ce_task = _poll_ce_task(host_url, task_id, token)
    if not ce_ok:
        report = make_report(
            technique_code=tech,
            metric_code=metric,
            branch_name=folder,
            branch_type=branch_type,
            version=version,
            tool_name="SonarQube Community",
            source="sonar",
            status="ERROR",
            raw_summary="CE task failed: %s" % ce_task.get("status", "?"),
            extra={"tool_log": "\n".join(log_parts)[-4000:], "ce_task": ce_task},
        )
        return report, "\n".join(log_parts)

    measures, err = _fetch_measures(host_url, project_key, token)
    if err and not measures:
        report = make_report(
            technique_code=tech,
            metric_code=metric,
            branch_name=folder,
            branch_type=branch_type,
            version=version,
            tool_name="SonarQube Community",
            source="sonar",
            status="ERROR",
            raw_summary=err,
            extra={"tool_log": "\n".join(log_parts)[-4000:]},
        )
        return report, "\n".join(log_parts)

    report = sonar_report_from_measures(
        measures,
        tech,
        metric,
        folder,
        branch_type,
        version,
        log="\n".join(log_parts),
        project_key=project_key,
    )
    return report, "\n".join(log_parts)


def run_sonar_batch(
    branches,
    build_dir="build",
    root=None,
    progress_callback=None,
    host_url=None,
    token=None,
):
    """Ensure server + token, scan each branch, return list of result rows."""
    repo_root = Path(root or ROOT)
    ok, host_url, msg = ensure_sonar_server(root=repo_root)
    if not ok:
        return [{
            "branch_name": b,
            "status": "ERROR",
            "error": msg,
        } for b in branches]

    try:
        token = token or ensure_sonar_token(host_url, root=repo_root)
    except Exception as exc:
        return [{
            "branch_name": b,
            "status": "ERROR",
            "error": str(exc),
        } for b in branches]

    results = []
    total = len(branches)
    for idx, bname in enumerate(branches, start=1):
        if progress_callback:
            progress_callback("sonar", idx - 1, total, bname, "starting")
        row = {"branch_name": bname, "server_msg": msg}
        branch_path = repo_root / build_dir / bname
        try:
            report, log = run_sonar_for_branch(
                branch_path,
                host_url=host_url,
                token=token,
                root=repo_root,
            )
            row["sonar_report"] = report
            row["status"] = report.get("status", "OK")
            row["tool_log"] = log
            row["coverage_pct"] = (report.get("metric_values") or {}).get("coverage_pct")
            if progress_callback:
                progress_callback("sonar", idx, total, bname, row["status"])
        except Exception as exc:
            row["status"] = "ERROR"
            row["error"] = str(exc)
            if progress_callback:
                progress_callback("sonar", idx, total, bname, "error: %s" % exc)
        results.append(row)
    return results
