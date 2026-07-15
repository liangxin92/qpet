#!/usr/bin/env python3
"""Validate a Codex v2 pet package and its PNG or WebP spritesheet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


EXPECTED_VERSION = 2
EXPECTED_SIZE = (1536, 2288)
EXPECTED_MODE = "RGBA"
EXPECTED_FORMATS = ("PNG", "WEBP")
EXPECTED_FORMAT = EXPECTED_FORMATS[0]
MAX_FILE_BYTES = 20 * 1024 * 1024

EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_OPERATIONAL_ERROR = 2


def _issue(code: str, message: str, path: Path | None = None) -> dict[str, str]:
    result = {"code": code, "message": message}
    if path is not None:
        result["path"] = str(path)
    return result


def _is_inside(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def inspect_metadata(
    metadata: Any, package_dir: Path
) -> tuple[Path | None, dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    """Validate pet.json data and resolve its spritesheet without touching Pillow."""
    checks: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(metadata, dict):
        errors.append(_issue("pet_json_not_object", "pet.json must contain a JSON object"))
        checks["metadata_object"] = False
        return None, checks, errors, warnings
    checks["metadata_object"] = True

    version = metadata.get("spriteVersionNumber")
    version_ok = type(version) is int and version == EXPECTED_VERSION
    checks["sprite_version"] = {
        "ok": version_ok,
        "actual": version,
        "expected": EXPECTED_VERSION,
    }
    if not version_ok:
        errors.append(
            _issue(
                "invalid_sprite_version",
                f"spriteVersionNumber must be the integer {EXPECTED_VERSION}",
            )
        )

    path_value = metadata.get("spritesheetPath")
    if not isinstance(path_value, str) or not path_value.strip():
        checks["spritesheet_path"] = {"ok": False, "actual": path_value}
        errors.append(
            _issue("missing_spritesheet_path", "spritesheetPath must be a non-empty string")
        )
        return None, checks, errors, warnings

    relative_path = Path(path_value)
    if relative_path.is_absolute():
        checks["spritesheet_path"] = {"ok": False, "actual": path_value}
        errors.append(
            _issue("absolute_spritesheet_path", "spritesheetPath must be relative to the package")
        )
        return None, checks, errors, warnings

    package_root = package_dir.resolve()
    sheet_path = (package_root / relative_path).resolve()
    inside = _is_inside(sheet_path, package_root) and sheet_path != package_root
    checks["spritesheet_path"] = {
        "ok": inside,
        "actual": path_value,
        "resolved": str(sheet_path),
    }
    if not inside:
        errors.append(
            _issue(
                "spritesheet_path_escape",
                "spritesheetPath must not escape the package directory",
                sheet_path,
            )
        )
        return None, checks, errors, warnings

    display_name = metadata.get("displayName", metadata.get("name"))
    display_name_ok = isinstance(display_name, str) and bool(display_name.strip())
    checks["display_name"] = {
        "ok": display_name_ok,
        "actual": display_name,
        "accepted_fields": ["displayName", "name"],
    }
    if not display_name_ok:
        warnings.append(
            _issue(
                "missing_display_name",
                "pet.json has no non-empty displayName (or legacy name)",
            )
        )
    return sheet_path, checks, errors, warnings


def inspect_image(
    sheet_path: Path, image_module: Any
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    checks: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    is_file = sheet_path.is_file()
    checks["spritesheet_file"] = {"ok": is_file, "path": str(sheet_path)}
    if not is_file:
        errors.append(_issue("spritesheet_missing", "spritesheet file does not exist", sheet_path))
        return checks, errors

    try:
        file_size = sheet_path.stat().st_size
    except OSError as exc:
        errors.append(_issue("spritesheet_stat_failed", str(exc), sheet_path))
        return checks, errors
    non_empty = file_size > 0
    checks["spritesheet_non_empty"] = {"ok": non_empty, "bytes": file_size}
    if not non_empty:
        errors.append(_issue("spritesheet_empty", "spritesheet file is empty", sheet_path))
        return checks, errors

    file_size_ok = file_size <= MAX_FILE_BYTES
    checks["file_size_limit"] = {
        "ok": file_size_ok,
        "bytes": file_size,
        "max_bytes": MAX_FILE_BYTES,
    }
    if not file_size_ok:
        errors.append(
            _issue(
                "spritesheet_too_large",
                f"spritesheet must not exceed {MAX_FILE_BYTES} bytes (20 MiB)",
                sheet_path,
            )
        )

    try:
        with image_module.open(sheet_path) as image:
            image.load()
            actual_size = tuple(image.size)
            actual_mode = image.mode
            actual_format = image.format
            alpha_extrema = image.getchannel("A").getextrema() if actual_mode == EXPECTED_MODE else None
    except Exception as exc:  # Pillow exposes multiple decoder-specific exception types.
        checks["image_decodable"] = False
        errors.append(_issue("spritesheet_not_decodable", str(exc), sheet_path))
        return checks, errors

    checks["image_decodable"] = True
    size_ok = actual_size == EXPECTED_SIZE
    mode_ok = actual_mode == EXPECTED_MODE
    format_ok = actual_format in EXPECTED_FORMATS
    transparency_ok = alpha_extrema is not None and alpha_extrema[0] < 255
    checks["dimensions"] = {
        "ok": size_ok,
        "actual": list(actual_size),
        "expected": list(EXPECTED_SIZE),
    }
    checks["color_mode"] = {
        "ok": mode_ok,
        "actual": actual_mode,
        "expected": EXPECTED_MODE,
    }
    checks["image_format"] = {
        "ok": format_ok,
        "actual": actual_format,
        "expected": list(EXPECTED_FORMATS),
    }
    checks["alpha_transparency"] = {
        "ok": transparency_ok,
        "alpha_extrema": list(alpha_extrema) if alpha_extrema is not None else None,
        "requirement": "at least one pixel with alpha below 255",
    }
    if not size_ok:
        errors.append(
            _issue(
                "invalid_dimensions",
                f"v2 spritesheet must be {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]} pixels",
                sheet_path,
            )
        )
    if not mode_ok:
        errors.append(
            _issue(
                "invalid_color_mode",
                f"spritesheet must use {EXPECTED_MODE} color mode",
                sheet_path,
            )
        )
    if not format_ok:
        errors.append(
            _issue("invalid_image_format", "spritesheet must be a PNG or WebP image", sheet_path)
        )
    if mode_ok and not transparency_ok:
        errors.append(
            _issue(
                "missing_transparency",
                "RGBA spritesheet must contain at least one transparent pixel",
                sheet_path,
            )
        )
    return checks, errors


def validate_package(package_dir: Path, image_module: Any) -> dict[str, Any]:
    root = package_dir.expanduser().resolve()
    pet_json = root / "pet.json"
    result: dict[str, Any] = {
        "valid": False,
        "package_dir": str(root),
        "pet_json": str(pet_json),
        "spritesheet": None,
        "checks": {},
        "errors": [],
        "warnings": [],
    }

    if not pet_json.is_file():
        result["checks"]["pet_json_file"] = False
        result["errors"].append(_issue("pet_json_missing", "pet.json does not exist", pet_json))
        return result
    result["checks"]["pet_json_file"] = True

    try:
        raw = pet_json.read_text(encoding="utf-8")
        metadata = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result["checks"]["pet_json_decodable"] = False
        result["errors"].append(_issue("pet_json_invalid", str(exc), pet_json))
        return result
    result["checks"]["pet_json_decodable"] = True

    sheet_path, metadata_checks, errors, warnings = inspect_metadata(metadata, root)
    result["checks"].update(metadata_checks)
    result["errors"].extend(errors)
    result["warnings"].extend(warnings)
    if sheet_path is not None:
        result["spritesheet"] = str(sheet_path)
        image_checks, image_errors = inspect_image(sheet_path, image_module)
        result["checks"].update(image_checks)
        result["errors"].extend(image_errors)

    result["valid"] = not result["errors"]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate pet.json and a 1536x2288 RGBA PNG/WebP v2 spritesheet."
    )
    parser.add_argument("package_dir", metavar="PACKAGE_DIR", help="Directory containing pet.json.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def _operational_result(package_dir: Path, code: str, message: str) -> dict[str, Any]:
    return {
        "valid": False,
        "package_dir": str(package_dir),
        "checks": {},
        "errors": [_issue(code, message, package_dir)],
        "warnings": [],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    package_dir = Path(args.package_dir).expanduser()
    if not package_dir.is_dir():
        result = _operational_result(
            package_dir.resolve(), "package_dir_missing", "PACKAGE_DIR does not exist or is not a directory"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return EXIT_OPERATIONAL_ERROR

    try:
        from PIL import Image
    except ImportError:
        result = _operational_result(
            package_dir.resolve(),
            "pillow_missing",
            "Pillow is required; run this script with the bundled Codex Python runtime",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return EXIT_OPERATIONAL_ERROR

    result = validate_package(package_dir, Image)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return EXIT_VALID if result["valid"] else EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
