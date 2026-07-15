#!/usr/bin/env python3
"""Safely construct a Codex pet-install deep link."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
from typing import Any, Sequence
from urllib.parse import quote, urlencode, urlsplit


DEEPLINK_BASE = "codex://pets/install"
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def _validated_text(value: str, field: str, max_length: int) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        raise ValueError(f"{field} cannot be empty")
    if _CONTROL_CHARACTERS.search(value):
        raise ValueError(f"{field} contains unsupported control characters")
    if len(cleaned) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")
    return cleaned


def _is_loopback_hostname(hostname: str) -> bool:
    normalized = hostname.rstrip(".").casefold()
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        try:
            address = ipaddress.IPv4Address(socket.inet_aton(normalized))
        except OSError:
            return False
    if address.is_loopback:
        return True
    mapped = getattr(address, "ipv4_mapped", None)
    return bool(mapped is not None and mapped.is_loopback)


def validate_https_image_url(value: str) -> str:
    cleaned = _validated_text(value, "image URL", 2048)
    try:
        parsed = urlsplit(cleaned)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError("image URL is malformed") from exc
    if parsed.scheme.lower() != "https":
        raise ValueError("image URL must use https")
    if not hostname:
        raise ValueError("image URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("image URL must not contain credentials")
    if _is_loopback_hostname(hostname):
        raise ValueError("image URL must not use localhost or a loopback address")
    if parsed.fragment:
        raise ValueError("image URL must not contain a fragment")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("image URL contains an invalid port") from exc
    return cleaned


def build_deeplink(
    *,
    name: str,
    image_url: str,
    description: str | None = None,
    sprite_version: int = 2,
) -> tuple[str, dict[str, Any]]:
    clean_name = _validated_text(name, "name", 80)
    clean_url = validate_https_image_url(image_url)
    if sprite_version not in (1, 2) or isinstance(sprite_version, bool):
        raise ValueError("sprite version must be 1 or 2")

    parameters: dict[str, Any] = {
        "name": clean_name,
        "imageUrl": clean_url,
    }
    if description is not None:
        parameters["description"] = _validated_text(description, "description", 500)
    parameters["spriteVersionNumber"] = sprite_version
    query = urlencode(parameters, doseq=False, quote_via=quote, safe="")
    return f"{DEEPLINK_BASE}?{query}", parameters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a safe codex://pets/install deep link.")
    parser.add_argument("--name", required=True, help="Pet display name.")
    parser.add_argument("--image-url", required=True, help="Public HTTPS spritesheet URL.")
    parser.add_argument("--description", help="Optional short pet description.")
    parser.add_argument(
        "--sprite-version",
        type=int,
        choices=(1, 2),
        default=2,
        help="Pet sprite version (default: 2).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print a JSON object instead of only the deep link.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        url, parameters = build_deeplink(
            name=args.name,
            image_url=args.image_url,
            description=args.description,
            sprite_version=args.sprite_version,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.pretty:
        print(json.dumps({"url": url, "parameters": parameters}, ensure_ascii=False, indent=2))
    else:
        print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
