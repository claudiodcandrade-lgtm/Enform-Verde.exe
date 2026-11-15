"""Fail CI when a tests/test_*.py module contributes zero unittest cases.

Bare pytest-style functions are invisible to ``python -m unittest discover``;
a module written that way reports "Ran 0 tests ... OK" and hides real
regressions (this happened to tests/test_fitofisionomia_intersections.py).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def count_cases(suite) -> int:
    total = 0
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            total += count_cases(item)
        else:
            if type(item).__name__ in {"_FailedTest", "ModuleImportFailure"}:
                raise RuntimeError(str(item))
            total += 1
    return total


def main() -> int:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tests"))
    loader = unittest.TestLoader()
    empty, broken = [], []
    files = sorted((ROOT / "tests").glob("test_*.py"))
    for path in files:
        try:
            n = count_cases(loader.loadTestsFromName(path.stem))
        except Exception as exc:  # import error, syntax error...
            broken.append(f"{path.name}: {type(exc).__name__}: {str(exc)[:300]}")
            continue
        if n == 0:
            empty.append(path.name)
    print(f"test modules inspected: {len(files)}")
    for name in empty:
        print("ZERO unittest cases collected:", name)
    for line in broken:
        print("IMPORT FAILURE:", line)
    return 1 if (empty or broken) else 0


if __name__ == "__main__":
    raise SystemExit(main())
