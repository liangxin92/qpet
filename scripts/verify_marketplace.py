#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN = ROOT / "plugins" / "qpet"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    return {}


def main() -> int:
    errors: list[str] = []
    marketplace = load_json(MARKETPLACE, errors)
    manifest = load_json(MANIFEST, errors)

    if marketplace.get("name") != "qpet":
        errors.append("marketplace name must be qpet")
    if marketplace.get("interface", {}).get("displayName") != "Qpet":
        errors.append("marketplace displayName must be Qpet")

    entries = marketplace.get("plugins", [])
    if len(entries) != 1:
        errors.append("marketplace must contain exactly one plugin entry")
    else:
        entry = entries[0]
        expected = {
            "name": "qpet",
            "source": {"source": "local", "path": "./plugins/qpet"},
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Productivity",
        }
        if entry != expected:
            errors.append("marketplace plugin entry does not match the canonical Qpet entry")

    if manifest.get("name") != "qpet":
        errors.append("plugin manifest name must match folder name qpet")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", manifest.get("version", "")):
        errors.append("plugin version must be semantic-version shaped")
    interface = manifest.get("interface", {})
    if interface.get("displayName") != "Qpet":
        errors.append("plugin displayName must be Qpet")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin skills path must be ./skills/")

    for field in ("composerIcon", "logo", "logoDark"):
        value = interface.get(field)
        if not isinstance(value, str) or not (PLUGIN / value).is_file():
            errors.append(f"missing or invalid interface asset: {field}")
    for value in interface.get("screenshots", []):
        if not isinstance(value, str) or not (PLUGIN / value).is_file():
            errors.append(f"missing screenshot: {value}")

    skill_file = PLUGIN / "skills" / "create-chibi-pet" / "SKILL.md"
    if not skill_file.is_file():
        errors.append("missing create-chibi-pet/SKILL.md")

    tests = load_json(PLUGIN / "submission" / "test-cases.json", errors)
    if len(tests.get("positive_tests", [])) != 5:
        errors.append("submission must contain exactly five positive tests")
    if len(tests.get("negative_tests", [])) != 3:
        errors.append("submission must contain exactly three negative tests")

    forbidden_names = {".DS_Store", "__pycache__"}
    secret_pattern = re.compile(
        r"(?:sk-[A-Za-z0-9_-]{16,}|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY)"
    )
    for path in PLUGIN.rglob("*"):
        if path.name in forbidden_names or path.suffix == ".pyc":
            errors.append(f"generated file must not be published: {path.relative_to(ROOT)}")
        if path.is_symlink():
            errors.append(f"symlink not allowed in release: {path.relative_to(ROOT)}")
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".py"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if secret_pattern.search(text):
                errors.append(f"possible secret in {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "valid",
                "marketplace": "qpet",
                "plugin": "qpet",
                "skill": "create-chibi-pet",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

