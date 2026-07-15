#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "plugins" / "qpet"


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy an approved development snapshot into the Qpet release repository."
    )
    parser.add_argument("source", type=Path, help="Development plugin root")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()

    if not (source / ".codex-plugin" / "plugin.json").is_file():
        raise SystemExit("source is not a plugin root")

    for directory in ("skills", "assets", "submission", "tests"):
        copy_tree(source / directory, DESTINATION / directory)
    for filename in ("LICENSE", "CHANGELOG.md"):
        shutil.copy2(source / filename, DESTINATION / filename)

    test_file = DESTINATION / "tests" / "test_submission_package.py"
    test_text = test_file.read_text(encoding="utf-8")
    test_text = test_text.replace(
        'self.assertEqual(manifest["name"], "chibi-pet-studio")',
        'self.assertEqual(manifest["name"], "qpet")',
    )
    test_file.write_text(test_text, encoding="utf-8")

    source_manifest = json.loads(
        (source / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    snapshot = {
        "source": str(source),
        "source_version": source_manifest.get("version"),
        "synced_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_plugin_id": "qpet",
    }
    (ROOT / "SNAPSHOT.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_marketplace.py")], check=True)
    print("Qpet snapshot synchronized and verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

