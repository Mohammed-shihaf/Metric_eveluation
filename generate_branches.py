#!/usr/bin/env python3
"""Generate metric branches from config/metrics_registry.yaml."""

from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from lib.generator import create_git_branches, generate_branches, push_branches  # noqa: E402
from lib.registry import iter_branches  # noqa: E402
from lib.validate import BranchValidationError, validate_build  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Generate technique/metric branches")
    p.add_argument("--techniques", default="all")
    p.add_argument("--metrics", default="all")
    p.add_argument("--types", default="Bug,BugFX,TCC,CC")
    p.add_argument("--language", default="python")
    p.add_argument("--version", default="2.6")
    p.add_argument("--out", default="build")
    p.add_argument("--git", action="store_true")
    p.add_argument("--push", action="store_true")
    p.add_argument("--skip-validate", action="store_true")
    args = p.parse_args()

    types = [t.strip() for t in args.types.split(",")]
    planned = list(iter_branches(args.techniques, args.metrics, types, args.version))
    print("Will generate %d branches" % len(planned))
    for tech, metric, bt, name in planned[:20]:
        print("  %s" % name)
    if len(planned) > 20:
        print("  ... and %d more" % (len(planned) - 20))

    names, gen_errors = generate_branches(
        args.techniques, args.metrics, types, args.version, args.language, args.out, ROOT,
        continue_on_error=False)
    print("\nGenerated %d branches under %s" % (len(names), os.path.join(ROOT, args.out)))
    if gen_errors:
        print("Generation errors: %d" % len(gen_errors), file=sys.stderr)
        for err in gen_errors:
            print("  %s: %s" % (err["branch"], err["error"]), file=sys.stderr)
        return 1

    if not args.skip_validate:
        results = validate_build(
            args.techniques, args.metrics, types, args.version, args.language, args.out, ROOT)
        for name, tech, metric, bt, loc, status in results:
            print("OK  %s  [%s]  LOC=%d" % (name, bt, loc))
        print("\nAll %d branches passed validation." % len(results))

    if args.git:
        create_git_branches(args.techniques, args.metrics, types, args.version, args.language, ROOT, args.out)
        if args.push:
            push_branches(names, ROOT)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BranchValidationError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
