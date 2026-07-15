#!/usr/bin/env python3
"""Check whether the local Codex pet-generation runtime is available."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence


EXIT_READY = 0
EXIT_MISSING_HATCH_PET = 2
EXIT_MISSING_IMAGEGEN = 4


def resolve_codex_home(override: str | None = None) -> Path:
    value = override or os.environ.get("CODEX_HOME")
    if value:
        return Path(value).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def _component_result(candidates: list[Path]) -> dict[str, Any]:
    found = next((path for path in candidates if path.is_file()), None)
    return {
        "available": found is not None,
        "path": str(found) if found is not None else None,
        "candidates": [str(path) for path in candidates],
    }


def inspect_runtime(codex_home: Path) -> tuple[dict[str, Any], int]:
    root = codex_home.expanduser().resolve()
    hatch = _component_result([root / "skills" / "hatch-pet" / "SKILL.md"])
    imagegen = _component_result(
        [
            root / "skills" / ".system" / "imagegen" / "SKILL.md",
            root / "skills" / "imagegen" / "SKILL.md",
        ]
    )
    exit_code = EXIT_READY
    if not hatch["available"]:
        exit_code |= EXIT_MISSING_HATCH_PET
    if not imagegen["available"]:
        exit_code |= EXIT_MISSING_IMAGEGEN

    result = {
        "ready": exit_code == EXIT_READY,
        "status": "ready" if exit_code == EXIT_READY else "incomplete",
        "codex_home": str(root),
        "components": {
            "hatch_pet": hatch,
            "imagegen": imagegen,
        },
        "exit_code": exit_code,
        "exit_code_meaning": {
            "0": "all required skills are available",
            "2": "hatch-pet is missing",
            "4": "imagegen is missing",
            "6": "hatch-pet and imagegen are both missing",
        }[str(exit_code)],
    }
    return result, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check for the hatch-pet and imagegen SKILL.md files."
    )
    parser.add_argument(
        "--codex-home",
        metavar="PATH",
        help="Override CODEX_HOME (default: $CODEX_HOME or ~/.codex).",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result, exit_code = inspect_runtime(resolve_codex_home(args.codex_home))
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
