"""Subprocess worker: run one branch tool assert inside an isolated venv."""

from __future__ import print_function

import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REPORT_START = "<<<REPORT>>>"
REPORT_END = "<<<END>>>"


def main():
    p = argparse.ArgumentParser(description="Run local tool for one branch (venv worker)")
    p.add_argument("--branch-path", required=True)
    p.add_argument("--technique", required=True)
    p.add_argument("--metric", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--version", default="2.6")
    p.add_argument("--language", default="")
    p.add_argument("--commit-sha", default="")
    p.add_argument("--run-id", default="")
    p.add_argument(
        "--require-real-tool",
        action="store_true",
        help="Fail if the registry primary tool cannot execute (no structural fallback)",
    )
    args = p.parse_args()

    from lib.local_tool_runner import run_local_tool_report

    from lib.lang_support import branch_language, normalize_language

    lang = normalize_language(args.language or branch_language(args.branch_path))

    report = run_local_tool_report(
        args.branch_path,
        args.technique,
        args.metric,
        args.type,
        args.version,
        language=lang,
        commit_sha=args.commit_sha or None,
        run_id=args.run_id or None,
        install=False,
        require_real_tool=args.require_real_tool,
    )
    print(REPORT_START)
    print(json.dumps(report))
    print(REPORT_END)
    return 0


if __name__ == "__main__":
    sys.exit(main())
