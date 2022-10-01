#!/usr/bin/python3
#
"""Extract an attribute of a Python module and print its value"""

import argparse
import ast
import sys
from contextlib import nullcontext


# Code adapted from setuptools/config/expand.py
def getattr_from_source(attr, src, name="<unknown>"):
    module = ast.parse(src, name)
    try:
        return next(
            ast.literal_eval(value)
            for target, value in _find_assignments(module)
            if isinstance(target, ast.Name) and target.id == attr)
    except Exception as e:
        raise AttributeError(f"{name} has no attribute {attr}") from e


def _find_assignments(module):
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                yield target, statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value:
            yield statement.target, statement.value


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attribute")
    parser.add_argument(
        "module", nargs="?",
        type=argparse.FileType(), default=nullcontext(sys.stdin),
        help="filename of Python module (default: stdin)")
    return parser


def main():
    args = build_parser().parse_args()
    with args.module as file:
        source = file.read()
    attr = getattr_from_source(args.attribute, source, name=file.name)
    print(attr, end="")


if __name__ == "__main__":
    main()
