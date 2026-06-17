"""Language generator dispatch."""

from __future__ import print_function

from lib.lang_generators import template_core

generate_branch_files = template_core.generate_branch_files
write_branch = template_core.write_branch

__all__ = ["generate_branch_files", "write_branch"]
