from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_ROOT / "skills" / "create-chibi-pet" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import build_install_deeplink  # noqa: E402
import check_runtime  # noqa: E402
import chibi_pet_spec  # noqa: E402
import validate_pet_package  # noqa: E402


class ChibiPetSpecTests(unittest.TestCase):
    def test_reproducible_and_visibly_distinct(self) -> None:
        kwargs = {
            "name": "露娜",
            "material": "磨砂陶瓷",
            "seed": "same-seed",
        }
        first = chibi_pet_spec.build_spec(["月亮兔，咖啡师", "咖啡师"], **kwargs)
        second = chibi_pet_spec.build_spec(["月亮兔", "咖啡师"], **kwargs)
        self.assertEqual(first, second)
        self.assertEqual(first["request"]["keywords"], ["月亮兔", "咖啡师"])
        self.assertEqual(len(first["concepts"]), 3)
        self.assertEqual(len({item["silhouette"] for item in first["concepts"]}), 3)
        self.assertEqual(len({item["palette"]["name"] for item in first["concepts"]}), 3)
        self.assertTrue(all("磨砂陶瓷" in item["material"] for item in first["concepts"]))
        self.assertTrue(all("3D Q版" in item["render_prompt"] for item in first["concepts"]))
        self.assertIn(first["recommended_concept_id"], {item["id"] for item in first["concepts"]})

    def test_default_seed_is_deterministic(self) -> None:
        first = chibi_pet_spec.build_spec(["forest", "robot"])
        second = chibi_pet_spec.build_spec(["forest", "robot"])
        self.assertEqual(first, second)
        self.assertLessEqual(first["request"]["seed"], (1 << 53) - 1)

    def test_user_seed_stays_within_javascript_safe_integer_range(self) -> None:
        spec = chibi_pet_spec.build_spec(["forest", "robot"], seed=(1 << 63) - 1)
        self.assertLessEqual(spec["request"]["seed"], (1 << 53) - 1)

    def test_mint_orbit_trial_constraints_are_preserved_in_every_concept(self) -> None:
        keywords = [
            "mint-green astronaut shiba",
            "soft-clay 3D chibi style",
            "curious personality",
            "with a tiny attached satchel",
        ]
        spec = chibi_pet_spec.build_spec(
            keywords,
            name="Mint Orbit",
            material="soft clay",
            seed="mint-orbit-concepts-v1",
        )
        rerun = chibi_pet_spec.build_spec(
            keywords,
            name="Mint Orbit",
            material="soft clay",
            seed="mint-orbit-concepts-v1",
        )
        self.assertEqual(spec, rerun)
        self.assertEqual(spec["request"]["language"], "en")
        self.assertEqual(spec["request"]["literal_core_constraints"], keywords)
        self.assertEqual(spec["request"]["required_color_cues"], ["mint-green"])
        self.assertEqual(spec["request"]["required_accessory"], ["satchel"])
        self.assertEqual(spec["identity_lock"]["status"], "pending_selection")
        self.assertTrue(spec["identity_lock"]["pending_selection"])
        self.assertNotIn("head_geometry", spec["identity_lock"])
        self.assertNotIn("face_construction", spec["identity_lock"])

        self.assertEqual(len({item["head_geometry"] for item in spec["concepts"]}), 3)
        self.assertEqual(len({item["face_construction"] for item in spec["concepts"]}), 3)
        self.assertEqual(len({item["palette"]["strategy"] for item in spec["concepts"]}), 3)
        self.assertEqual(len({item["palette"]["secondary"] for item in spec["concepts"]}), 3)
        self.assertEqual(len({item["palette"]["accent"] for item in spec["concepts"]}), 3)
        self.assertEqual(
            {item["palette"]["ratios_percent"]["primary"] for item in spec["concepts"]},
            {50, 60, 70},
        )

        for concept in spec["concepts"]:
            self.assertEqual(concept["literal_core_constraints"], keywords)
            for keyword in keywords:
                self.assertIn(f'"{keyword}"', concept["render_prompt"])
            self.assertEqual(concept["required_color_cues"], ["mint-green"])
            self.assertEqual(concept["palette"]["primary"], "#8FE3C0")
            self.assertEqual(concept["required_accessory"], ["satchel"])
            self.assertTrue(concept["accessory"]["physically_attached"])
            self.assertIn("never hand-held", concept["accessory"]["construction"])
            self.assertEqual(concept["material_core"], "soft clay")
            self.assertIn("soft clay", concept["render_prompt"])

        markdown = chibi_pet_spec.render_markdown(spec)
        self.assertIn("## Identity lock status", markdown)
        self.assertIn("Status: `pending_selection`", markdown)
        for keyword in keywords:
            self.assertGreaterEqual(markdown.count(keyword), 7)
        for concept in spec["concepts"]:
            self.assertIn(f"- Head geometry: {concept['head_geometry']}", markdown)
            self.assertIn(f"- Face construction: {concept['face_construction']}", markdown)
        self.assertNotRegex(markdown, r"[\u3400-\u4dbf\u4e00-\u9fff]")

    def test_common_color_cues_are_canonicalized(self) -> None:
        cases = {
            "mint": "mint-green",
            "mint-green": "mint-green",
            "薄荷绿": "mint-green",
            "blue": "blue",
            "red": "red",
            "purple": "purple",
            "green": "green",
            "黑白": "black-white",
            "black and white": "black-white",
        }
        for keyword, expected in cases.items():
            with self.subTest(keyword=keyword):
                spec = chibi_pet_spec.build_spec([keyword, "robot"], seed="colors")
                self.assertIn(expected, spec["request"]["required_color_cues"])
                self.assertTrue(
                    all(expected in item["palette"]["required_color_cues"] for item in spec["concepts"])
                )

    def test_common_accessories_remain_attached_in_all_directions(self) -> None:
        cases = {
            "tiny satchel": "satchel",
            "小挎包": "satchel",
            "backpack": "backpack",
            "眼镜": "glasses",
            "round glasses": "glasses",
            "red scarf": "scarf",
        }
        for keyword, expected in cases.items():
            with self.subTest(keyword=keyword):
                spec = chibi_pet_spec.build_spec(["fox", keyword], seed="accessories")
                self.assertIn(expected, spec["request"]["required_accessory"])
                for concept in spec["concepts"]:
                    self.assertIn(expected, concept["required_accessory"])
                    self.assertTrue(concept["accessory"]["physically_attached"])
                    self.assertIn(keyword, concept["render_prompt"])
                    if spec["request"]["language"] == "en":
                        self.assertIn(expected, concept["render_prompt"])

    def test_rejects_empty_keywords(self) -> None:
        with self.assertRaisesRegex(ValueError, "keyword"):
            chibi_pet_spec.build_spec([" , ；\n"])

    def test_selfie_and_reference_likeness_modes(self) -> None:
        selfie = chibi_pet_spec.build_spec(
            ["太空探险家"], source_mode="selfie", seed="portrait"
        )
        self.assertEqual(selfie["request"]["source_mode"], "selfie")
        self.assertEqual(selfie["request"]["likeness_cues"], [])
        self.assertEqual(selfie["identity_lock"]["likeness_lock"]["cues"], [])

        reference = chibi_pet_spec.build_spec(
            ["森林守护者"],
            source_mode="reference",
            likeness_cues=["保留左耳月牙标记", " 保留左耳月牙标记 ", "蓝绿色眼睛"],
            seed="portrait",
        )
        self.assertEqual(
            reference["identity_lock"]["likeness_lock"]["cues"],
            ["保留左耳月牙标记", "蓝绿色眼睛"],
        )
        self.assertTrue(all("蓝绿色眼睛" in item["render_prompt"] for item in reference["concepts"]))
        markdown = chibi_pet_spec.render_markdown(reference)
        self.assertIn("来源模式：reference", markdown)
        self.assertIn("相似性提示：保留左耳月牙标记、蓝绿色眼睛", markdown)
        self.assertIn("（推荐）", markdown)

    def test_likeness_cue_limits_and_source_mode_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "at most 8"):
            chibi_pet_spec.build_spec(
                ["robot"], source_mode="reference", likeness_cues=[f"cue-{i}" for i in range(9)]
            )
        with self.assertRaisesRegex(ValueError, "at most 120"):
            chibi_pet_spec.build_spec(
                ["robot"], source_mode="reference", likeness_cues=["x" * 121]
            )
        with self.assertRaisesRegex(ValueError, "source mode"):
            chibi_pet_spec.build_spec(["robot"], source_mode="unknown")

    def test_markdown_and_output_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            json_path = Path(temporary) / "brief.json"
            markdown_path = Path(temporary) / "brief.md"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = chibi_pet_spec.main(
                    [
                        "--keywords",
                        "云朵狐狸, 飞行员",
                        "--seed",
                        "42",
                        "--source-mode",
                        "selfie",
                        "--likeness-cue",
                        "保留圆框眼镜",
                        "--format",
                        "json",
                        "--json-out",
                        str(json_path),
                        "--markdown-out",
                        str(markdown_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload, json.loads(json_path.read_text(encoding="utf-8")))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("## 概念 1", markdown)
            self.assertIn("## 身份锁状态", markdown)
            self.assertIn("来源模式：selfie", markdown)
            self.assertEqual(payload["request"]["likeness_cues"], ["保留圆框眼镜"])


class RuntimeCheckTests(unittest.TestCase):
    def test_exit_codes_are_bit_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            result, code = check_runtime.inspect_runtime(codex_home)
            self.assertEqual(code, 6)
            self.assertFalse(result["ready"])

            hatch = codex_home / "skills" / "hatch-pet" / "SKILL.md"
            hatch.parent.mkdir(parents=True)
            hatch.write_text("hatch", encoding="utf-8")
            _, code = check_runtime.inspect_runtime(codex_home)
            self.assertEqual(code, 4)

            imagegen = codex_home / "skills" / ".system" / "imagegen" / "SKILL.md"
            imagegen.parent.mkdir(parents=True)
            imagegen.write_text("imagegen", encoding="utf-8")
            result, code = check_runtime.inspect_runtime(codex_home)
            self.assertEqual(code, 0)
            self.assertTrue(result["ready"])
            self.assertEqual(result["components"]["hatch_pet"]["path"], str(hatch.resolve()))

    def test_cli_returns_missing_code_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = check_runtime.main(["--codex-home", temporary])
            self.assertEqual(exit_code, 6)
            self.assertEqual(json.loads(stdout.getvalue())["exit_code"], 6)


class InstallDeeplinkTests(unittest.TestCase):
    def test_encodes_every_user_value_without_query_injection(self) -> None:
        source_url = "https://cdn.example.com/pet sheet.png?token=a&size=2"
        deeplink, _ = build_install_deeplink.build_deeplink(
            name="月兔 & 朋友?#",
            image_url=source_url,
            description="会挥手，也会等待 & 思考",
            sprite_version=2,
        )
        parsed = urlsplit(deeplink)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ("codex", "pets", "/install"))
        query = parse_qs(parsed.query, strict_parsing=True)
        self.assertEqual(query["name"], ["月兔 & 朋友?#"])
        self.assertEqual(query["imageUrl"], [source_url])
        self.assertEqual(query["description"], ["会挥手，也会等待 & 思考"])
        self.assertEqual(query["spriteVersionNumber"], ["2"])

    def test_rejects_unsafe_image_urls(self) -> None:
        invalid_urls = (
            "http://example.com/pet.png",
            "https://user:secret@example.com/pet.png",
            "https://example.com/pet.png#fragment",
            "https://example.com/pet.png\nnext",
            "https://localhost/pet.webp",
            "https://assets.localhost/pet.webp",
            "https://localhost./pet.webp",
            "https://127.0.0.1/pet.webp",
            "https://127.42.10.8/pet.webp",
            "https://127.1/pet.webp",
            "https://[::1]/pet.webp",
            "https://[::ffff:127.0.0.1]/pet.webp",
        )
        for value in invalid_urls:
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_install_deeplink.build_deeplink(name="Pet", image_url=value)

    def test_description_is_optional(self) -> None:
        deeplink, parameters = build_install_deeplink.build_deeplink(
            name="Pet", image_url="https://example.com/pet.png"
        )
        self.assertNotIn("description", parameters)
        self.assertNotIn("description=", deeplink)


class _FakeImage:
    def __init__(
        self,
        *,
        size: tuple[int, int] = validate_pet_package.EXPECTED_SIZE,
        mode: str = validate_pet_package.EXPECTED_MODE,
        image_format: str = validate_pet_package.EXPECTED_FORMAT,
        alpha_extrema: tuple[int, int] = (0, 255),
    ) -> None:
        self.size = size
        self.mode = mode
        self.format = image_format
        self.alpha_extrema = alpha_extrema

    def __enter__(self) -> "_FakeImage":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def load(self) -> None:
        return None

    def getchannel(self, channel: str) -> "_FakeImage":
        if channel != "A":
            raise ValueError(channel)
        return self

    def getextrema(self) -> tuple[int, int]:
        return self.alpha_extrema


class _FakeImageModule:
    def __init__(self, image: _FakeImage | None = None) -> None:
        self.image = image or _FakeImage()

    def open(self, path: Path) -> _FakeImage:
        return self.image


class PetPackageValidatorTests(unittest.TestCase):
    @staticmethod
    def _write_package(root: Path, metadata: dict[str, object] | None = None) -> None:
        payload = metadata or {
            "displayName": "Luna",
            "spritesheetPath": "spritesheet.png",
            "spriteVersionNumber": 2,
        }
        (root / "pet.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        sheet_path = root / str(payload["spritesheetPath"])
        sheet_path.parent.mkdir(parents=True, exist_ok=True)
        sheet_path.write_bytes(b"not-empty; fake decoder is injected")

    def test_valid_package_with_test_decoder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root)
            result = validate_pet_package.validate_package(root, _FakeImageModule())
            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])
            self.assertTrue(result["checks"]["dimensions"]["ok"])
            self.assertTrue(result["checks"]["color_mode"]["ok"])
            self.assertTrue(result["checks"]["alpha_transparency"]["ok"])
            self.assertEqual(result["warnings"], [])

    def test_display_name_is_the_primary_supported_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(
                root,
                {
                    "displayName": "Mint Orbit",
                    "spritesheetPath": "spritesheet.png",
                    "spriteVersionNumber": 2,
                },
            )
            result = validate_pet_package.validate_package(root, _FakeImageModule())
            self.assertTrue(result["checks"]["display_name"]["ok"])
            self.assertEqual(result["warnings"], [])

    def test_accepts_hatch_pet_default_webp_with_test_decoder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(
                root,
                {
                    "name": "Luna",
                    "spritesheetPath": "spritesheet.webp",
                    "spriteVersionNumber": 2,
                },
            )
            result = validate_pet_package.validate_package(
                root, _FakeImageModule(_FakeImage(image_format="WEBP"))
            )
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["checks"]["image_format"]["expected"], ["PNG", "WEBP"])

    def test_rejects_wrong_dimensions_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root)
            decoder = _FakeImageModule(_FakeImage(size=(8, 11), mode="RGB"))
            result = validate_pet_package.validate_package(root, decoder)
            self.assertFalse(result["valid"])
            codes = {item["code"] for item in result["errors"]}
            self.assertIn("invalid_dimensions", codes)
            self.assertIn("invalid_color_mode", codes)

    def test_rejects_unexpected_image_format(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root)
            result = validate_pet_package.validate_package(
                root, _FakeImageModule(_FakeImage(image_format="JPEG"))
            )
            self.assertFalse(result["valid"])
            self.assertIn("invalid_image_format", {item["code"] for item in result["errors"]})

    def test_rejects_fully_opaque_spritesheet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root)
            result = validate_pet_package.validate_package(
                root, _FakeImageModule(_FakeImage(alpha_extrema=(255, 255)))
            )
            self.assertFalse(result["valid"])
            self.assertIn("missing_transparency", {item["code"] for item in result["errors"]})

    def test_rejects_spritesheet_over_20_mib(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root)
            with (root / "spritesheet.png").open("r+b") as spritesheet:
                spritesheet.truncate(validate_pet_package.MAX_FILE_BYTES + 1)
            result = validate_pet_package.validate_package(root, _FakeImageModule())
            self.assertFalse(result["valid"])
            self.assertIn("spritesheet_too_large", {item["code"] for item in result["errors"]})

    def test_rejects_path_escape_and_non_v2_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = {
                "spritesheetPath": "../outside.png",
                "spriteVersionNumber": 1,
            }
            sheet_path, checks, errors, _ = validate_pet_package.inspect_metadata(metadata, root)
            self.assertIsNone(sheet_path)
            self.assertFalse(checks["sprite_version"]["ok"])
            codes = {item["code"] for item in errors}
            self.assertEqual(codes, {"invalid_sprite_version", "spritesheet_path_escape"})

    def test_real_pillow_png_and_webp_when_available(self) -> None:
        try:
            from PIL import Image, features
        except ImportError:
            self.skipTest("Pillow is not installed in this Python runtime")
        formats = [("png", "PNG", {})]
        if features.check("webp"):
            formats.append(("webp", "WEBP", {"lossless": True}))
        for extension, image_format, save_options in formats:
            with self.subTest(image_format=image_format), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                sheet_name = f"spritesheet.{extension}"
                (root / "pet.json").write_text(
                    json.dumps(
                        {
                            "displayName": "Luna",
                            "spritesheetPath": sheet_name,
                            "spriteVersionNumber": 2,
                        }
                    ),
                    encoding="utf-8",
                )
                Image.new("RGBA", validate_pet_package.EXPECTED_SIZE, (0, 0, 0, 0)).save(
                    root / sheet_name, format=image_format, **save_options
                )
                result = validate_pet_package.validate_package(root, Image)
                self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
