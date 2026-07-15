#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "qpet"
SKILL = PLUGIN / "skills" / "create-chibi-pet"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".DS_Store" or path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        yield path


def write_tree(archive: Path, source: Path, archive_root: str) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in iter_files(source):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(f"{archive_root}/{relative}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic Qpet release archives.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_marketplace.py")], check=True)
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = manifest["version"].split("+", 1)[0]

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    plugin_zip = output / f"qpet-plugin-{version}.zip"
    skill_zip = output / f"qpet-skill-{version}.zip"
    write_tree(plugin_zip, PLUGIN, "qpet")
    write_tree(skill_zip, SKILL, "create-chibi-pet")

    checksum_file = output / "SHA256SUMS.txt"
    checksum_file.write_text(
        f"{sha256(plugin_zip)}  {plugin_zip.name}\n"
        f"{sha256(skill_zip)}  {skill_zip.name}\n",
        encoding="utf-8",
    )
    print(plugin_zip)
    print(skill_zip)
    print(checksum_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

