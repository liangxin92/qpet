from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SubmissionPackageTests(unittest.TestCase):
    def test_manifest_and_brand_assets(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "qpet")
        self.assertRegex(
            manifest["version"],
            r"^1\.0\.1(?:\+codex\.[0-9A-Za-z.-]+)?$",
        )
        interface = manifest["interface"]
        for field in ("composerIcon", "logo", "logoDark"):
            asset = (ROOT / interface[field]).resolve()
            self.assertTrue(asset.is_file(), f"missing {field}: {asset}")
            self.assertTrue(asset.is_relative_to(ROOT.resolve()))

    def test_exact_review_case_counts(self) -> None:
        cases = json.loads((ROOT / "submission" / "test-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cases["positive_tests"]), 5)
        self.assertEqual(len(cases["negative_tests"]), 3)
        ids = [case["id"] for group in ("positive_tests", "negative_tests") for case in cases[group]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_submission_copy_exists(self) -> None:
        required = (
            "marketplace-listing.md",
            "privacy-policy.md",
            "terms-of-use.md",
            "support.md",
            "review-notes.md",
            "release-notes.md",
            "portal-checklist.md",
            "website-copy.md",
        )
        for name in required:
            path = ROOT / "submission" / name
            self.assertTrue(path.is_file(), f"missing submission file: {name}")
            self.assertGreater(path.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
