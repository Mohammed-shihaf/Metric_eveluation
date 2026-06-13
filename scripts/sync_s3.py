#!/usr/bin/env python3
"""Download S3 tool reports aligned with taxonomy HTML on disk."""

from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

DEFAULT_CLASSIFICATION = os.path.join(ROOT, "taxonomy_reports", "Data Flow Testing")


def _load_env_force(path):
    """Load .env.local; AWS_* keys always override (fresh session tokens)."""
    from lib.sa_qa import load_env

    load_env(path)
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            k, v = key.strip(), val.strip()
            if k.startswith("AWS_") and v:
                os.environ[k] = v


def main():
    parser = argparse.ArgumentParser(description="Sync S3 tool bundles from taxonomy reports")
    parser.add_argument("--env-file", default=os.path.join(ROOT, ".env.local"))
    parser.add_argument("--classification-dir", default=DEFAULT_CLASSIFICATION)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _load_env_force(args.env_file)
    os.environ.setdefault("S3_SYNC_BRANCH_PREFIX", "DF_")

    from lib.s3_sync import backfill_missing

    print("S3 sync: %s" % args.classification_dir)
    try:
        summaries = backfill_missing(args.classification_dir, dry_run=args.dry_run)
    except Exception as exc:
        err = str(exc)
        if "ExpiredToken" in err:
            print("ERROR: AWS credentials expired.", file=sys.stderr)
            print("  Update ~/.aws/credentials or add fresh AWS_ACCESS_KEY_ID /", file=sys.stderr)
            print("  AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN to .env.local", file=sys.stderr)
        raise

    rc = 0
    for s in summaries:
        print("  %s: %s  files=%s  %s" % (
            s.get("branch"),
            s.get("status"),
            s.get("files_downloaded", ""),
            s.get("local_path", s.get("reason", s.get("skipped", ""))),
        ))
        if s.get("status") not in ("OK", "DRY_RUN") and not s.get("skipped"):
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
