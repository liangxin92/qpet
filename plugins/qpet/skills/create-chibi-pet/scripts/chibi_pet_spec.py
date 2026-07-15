#!/usr/bin/env python3
"""Build a deterministic, constraint-faithful three-direction 3D chibi pet brief."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA_VERSION = "1.1"
SOURCE_MODES = ("keywords", "selfie", "reference")
LANGUAGES = ("auto", "zh", "en")
MAX_LIKENESS_CUES = 8
MAX_LIKENESS_CUE_LENGTH = 120

_SPLIT_KEYWORDS = re.compile(r"[,，;；|\n]+")
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

_COLOR_RULES = (
    (
        "black-white",
        (
            r"(?<![a-z])black(?:\s+and\s+white|[-_\s]white)(?![a-z])",
            r"黑白(?:配色|色)?",
        ),
    ),
    (
        "mint-green",
        (
            r"(?<![a-z])mint(?:[-_\s]?green)?(?![a-z])",
            r"薄荷(?:绿(?:色)?|色)?",
        ),
    ),
    ("blue", (r"(?<![a-z])blue(?![a-z])", r"蓝色|蓝")),
    ("red", (r"(?<![a-z])red(?![a-z])", r"红色|红")),
    ("purple", (r"(?<![a-z])(?:purple|violet)(?![a-z])", r"紫色|紫")),
    ("green", (r"(?<![a-z])green(?![a-z])", r"绿色|绿")),
    ("black", (r"(?<![a-z])black(?![a-z])", r"黑色|黑")),
    ("white", (r"(?<![a-z])white(?![a-z])", r"白色|白")),
    ("yellow", (r"(?<![a-z])yellow(?![a-z])", r"黄色|黄")),
    ("orange", (r"(?<![a-z])orange(?![a-z])", r"橙色|橘色|橙|橘")),
    ("pink", (r"(?<![a-z])pink(?![a-z])", r"粉色|粉红色|粉红|粉")),
    ("cyan", (r"(?<![a-z])cyan(?![a-z])", r"青色|青")),
    ("teal", (r"(?<![a-z])teal(?![a-z])", r"蓝绿色|青绿(?:色)?")),
    ("brown", (r"(?<![a-z])brown(?![a-z])", r"棕色|褐色|棕|褐")),
    ("gray", (r"(?<![a-z])gr[ae]y(?![a-z])", r"灰色|灰")),
    ("gold", (r"(?<![a-z])gold(?:en)?(?![a-z])", r"金色|金")),
    ("silver", (r"(?<![a-z])silver(?![a-z])", r"银色|银")),
)

_COLOR_INFO: dict[str, dict[str, str]] = {
    "black-white": {"zh": "黑白", "en": "black and white", "hex": "#202124 + #F7F7F2"},
    "mint-green": {"zh": "薄荷绿", "en": "mint green", "hex": "#8FE3C0"},
    "blue": {"zh": "蓝色", "en": "blue", "hex": "#4D86E8"},
    "red": {"zh": "红色", "en": "red", "hex": "#E85656"},
    "purple": {"zh": "紫色", "en": "purple", "hex": "#8B6BD6"},
    "green": {"zh": "绿色", "en": "green", "hex": "#57B978"},
    "black": {"zh": "黑色", "en": "black", "hex": "#202124"},
    "white": {"zh": "白色", "en": "white", "hex": "#F7F7F2"},
    "yellow": {"zh": "黄色", "en": "yellow", "hex": "#F4C84A"},
    "orange": {"zh": "橙色", "en": "orange", "hex": "#ED8B45"},
    "pink": {"zh": "粉色", "en": "pink", "hex": "#F296B6"},
    "cyan": {"zh": "青色", "en": "cyan", "hex": "#54C7D9"},
    "teal": {"zh": "蓝绿色", "en": "teal", "hex": "#3FA9A3"},
    "brown": {"zh": "棕色", "en": "brown", "hex": "#9A6847"},
    "gray": {"zh": "灰色", "en": "gray", "hex": "#8D939C"},
    "gold": {"zh": "金色", "en": "gold", "hex": "#D9AD3F"},
    "silver": {"zh": "银色", "en": "silver", "hex": "#B7BEC8"},
}

_ACCESSORY_RULES = (
    ("satchel", (r"(?<![a-z])satchels?(?![a-z])", r"挎包|斜挎包")),
    ("backpack", (r"(?<![a-z])(?:backpacks?|rucksacks?)(?![a-z])", r"背包")),
    (
        "glasses",
        (r"(?<![a-z])(?:glasses|eyeglasses|spectacles)(?![a-z])", r"眼镜"),
    ),
    ("scarf", (r"(?<![a-z])(?:scarf|scarves)(?![a-z])", r"围巾")),
)

_ACCESSORY_NAMES: dict[str, dict[str, str]] = {
    "satchel": {"zh": "挎包", "en": "satchel"},
    "backpack": {"zh": "背包", "en": "backpack"},
    "glasses": {"zh": "眼镜", "en": "glasses"},
    "scarf": {"zh": "围巾", "en": "scarf"},
}

_ACCESSORY_ATTACHMENTS: dict[str, tuple[dict[str, str], ...]] = {
    "satchel": (
        {
            "zh": "同类挎包以清晰的斜跨带固定在右侧髋部，包体贴身且不由手持",
            "en": "the same satchel class is fixed at the right hip by a visible cross-body strap; it stays body-mounted and is never hand-held",
        },
        {
            "zh": "同类挎包以宽软带和腰侧短环固定在左侧，保留贴身下垂感且不由手持",
            "en": "the same satchel class is secured at the left waist with a broad soft strap and short belt loop; it hangs against the body and is never hand-held",
        },
        {
            "zh": "同类挎包通过一体式背带导轨扣合在后侧髋部，几何更紧凑但仍清楚可辨且不由手持",
            "en": "the same satchel class docks at the rear hip through an integrated harness rail; its geometry is compact but unmistakable and never hand-held",
        },
    ),
    "backpack": (
        {
            "zh": "同类背包以双肩带和胸前扣固定，完整贴附背部",
            "en": "the same backpack class is physically secured to the back with two shoulder straps and a chest clasp",
        },
        {
            "zh": "同类背包以柔软宽肩带和下方腰扣固定，轮廓圆润但不可拆失",
            "en": "the same backpack class is attached with broad soft shoulder straps and a lower waist buckle; its silhouette is rounder but it cannot disappear",
        },
        {
            "zh": "同类背包以紧凑硬壳背架和可见锁扣固定在背部",
            "en": "the same backpack class is mounted to the back on a compact hard-shell frame with visible locking tabs",
        },
    ),
    "glasses": (
        {
            "zh": "同类眼镜通过鼻梁和双侧镜腿稳定贴附面部",
            "en": "the same glasses class remains physically seated on the face through its bridge and two temple arms",
        },
        {
            "zh": "同类眼镜使用圆润镜框、鼻托和耳侧短带稳定固定",
            "en": "the same glasses class uses rounded rims, nose pads, and a short ear-side retainer to stay attached",
        },
        {
            "zh": "同类眼镜采用更紧凑的护目镜几何，以可见侧扣固定在头部",
            "en": "the same glasses class takes on compact goggle geometry and stays attached through visible side clasps",
        },
    ),
    "scarf": (
        {
            "zh": "同类围巾围绕颈部一圈并以短结固定，尾端保持简洁",
            "en": "the same scarf class wraps once around the neck and is physically secured with a short knot",
        },
        {
            "zh": "同类围巾以柔软宽环贴合颈肩，并由隐藏按扣固定",
            "en": "the same scarf class forms a broad soft neck loop held in place by a concealed snap",
        },
        {
            "zh": "同类围巾以紧凑领巾形态环绕颈部，并以可见侧扣固定",
            "en": "the same scarf class becomes a compact neckerchief physically anchored by a visible side clasp",
        },
    ),
}

_ARCHETYPES = (
    {
        "id": "concept-a",
        "title": {"zh": "收藏级玩具英雄", "en": "Collectible Toy Hero"},
        "direction": {
            "zh": "利落、明亮、稳定的精品玩具方向，以清楚剪影和克制细节建立辨识度。",
            "en": "A crisp, bright collectible-toy direction built around a stable silhouette and restrained detail.",
        },
        "silhouette": {
            "zh": "大圆头配胶囊形短身，手脚像圆润积木，整体重心稳定",
            "en": "a large round head over a short capsule body, with rounded block-like hands and feet",
        },
        "proportions": {
            "head_to_body": "1.75:1",
            "limbs": {"zh": "短而粗", "en": "short, sturdy limbs"},
            "stance": {"zh": "稳定宽站姿", "en": "a stable wide stance"},
        },
        "head_geometry": {
            "zh": "柔和方圆头，额头宽、下颌短，左右轮廓近乎对称",
            "en": "a soft rounded-square head with a broad forehead, short jaw, and near-symmetrical sides",
        },
        "face_construction": {
            "zh": "宽间距水滴眼、极短鼻口和两枚对称圆形颊部高光",
            "en": "wide-set teardrop eyes, an ultra-short muzzle, and two symmetrical round cheek highlights",
        },
        "default_material": {"zh": "高光搪胶", "en": "glossy vinyl"},
        "material_treatment": {
            "zh": "抛光压塑处理，主体平滑，边缘高光清晰",
            "en": "a polished compression-molded treatment with a smooth body and crisp edge highlights",
        },
        "palette_strategy": {
            "zh": "主色大色面：用户主色占 70%，辅色占 20%，点缀占 10%",
            "en": "dominant color field: 70% user primary, 20% secondary, 10% accent",
        },
        "ratios": {"primary": 70, "secondary": 20, "accent": 10},
        "pose": {
            "zh": "直立展示姿态；用目光、头部倾角和手势完整表达所有性格关键词",
            "en": "an upright presentation pose that expresses every personality constraint through gaze, head angle, and hand gesture",
        },
        "lighting": {
            "zh": "柔和摄影棚主光配细窄轮廓光",
            "en": "soft studio key light with a narrow rim light",
        },
    },
    {
        "id": "concept-b",
        "title": {"zh": "软雕塑幻想伙伴", "en": "Soft-Sculpted Storybook Companion"},
        "direction": {
            "zh": "柔软、亲近、有手作温度的故事书方向，以大体块和轻微不完美表达情绪。",
            "en": "A soft, approachable storybook direction whose broad forms and subtle imperfections carry emotion.",
        },
        "silhouette": {
            "zh": "梨形软身体配超大水滴头，肩线消失，双脚像两颗圆石",
            "en": "an oversized droplet head over a soft pear-shaped body, with no hard shoulder line and pebble-like feet",
        },
        "proportions": {
            "head_to_body": "1.9:1",
            "limbs": {"zh": "柔软短小", "en": "soft, tiny limbs"},
            "stance": {"zh": "内收放松站姿", "en": "a relaxed inward stance"},
        },
        "head_geometry": {
            "zh": "上宽下窄的软水滴头，双颊饱满，下巴收成小圆点",
            "en": "a soft top-heavy droplet head with full cheeks and a tiny rounded chin point",
        },
        "face_construction": {
            "zh": "低位大玻璃圆眼、小纽扣鼻和一侧不对称弧形腮红",
            "en": "low-set large glassy round eyes, a button nose, and one asymmetric curved blush mark",
        },
        "default_material": {"zh": "细腻软陶", "en": "fine soft clay"},
        "material_treatment": {
            "zh": "哑光手工捏塑处理，保留极轻压痕和柔和明暗",
            "en": "a matte hand-sculpted treatment with faint press marks and gentle shading",
        },
        "palette_strategy": {
            "zh": "同色阶分层：用户主色占 60%，低明度辅色占 25%，柔光点缀占 15%",
            "en": "tonal layering: 60% user primary, 25% lower-value secondary, 15% soft highlight accent",
        },
        "ratios": {"primary": 60, "secondary": 25, "accent": 15},
        "pose": {
            "zh": "温和前倾姿态；用目光、头部倾角和双手关系完整表达所有性格关键词",
            "en": "a gentle forward lean that expresses every personality constraint through gaze, head tilt, and hand relationship",
        },
        "lighting": {
            "zh": "大面积漫射窗光配温暖底光",
            "en": "broad diffused window light with a warm low fill",
        },
    },
    {
        "id": "concept-c",
        "title": {"zh": "未来软萌机灵鬼", "en": "Future-Soft Kinetic Buddy"},
        "direction": {
            "zh": "更大胆、更动感的未来伙伴方向，以紧凑结构和少量精准细节制造活力。",
            "en": "A bolder, more kinetic future-buddy direction using compact structure and a few precise details.",
        },
        "silhouette": {
            "zh": "圆角梯形躯干配悬浮感小手脚，头侧轮廓向外展开形成动势",
            "en": "a rounded trapezoid torso with tiny floating-feel limbs and outward-flaring head sides",
        },
        "proportions": {
            "head_to_body": "1.55:1",
            "limbs": {"zh": "小巧分离感", "en": "small, visually separated limbs"},
            "stance": {"zh": "不对称前冲站姿", "en": "an asymmetric forward-driving stance"},
        },
        "head_geometry": {
            "zh": "低矮圆角三角头，头顶略平，两侧形成短翼形转折",
            "en": "a low rounded-triangle head with a slightly flat crown and short wing-like side breaks",
        },
        "face_construction": {
            "zh": "斜向椭圆眼、单侧星点高光、窄小鼻梁和微露小虎牙",
            "en": "slanted oval eyes, a one-sided star glint, a narrow nose bridge, and one tiny visible fang",
        },
        "default_material": {"zh": "软触树脂", "en": "soft-touch resin"},
        "material_treatment": {
            "zh": "缎面壳体处理，转折处保留细窄高光和精确接缝",
            "en": "a satin shell treatment with narrow highlights and precise seams at structural breaks",
        },
        "palette_strategy": {
            "zh": "高对比色块：用户主色占 50%，深浅对比辅色占 30%，高能点缀占 20%",
            "en": "high-contrast blocking: 50% user primary, 30% contrast secondary, 20% energetic accent",
        },
        "ratios": {"primary": 50, "secondary": 30, "accent": 20},
        "pose": {
            "zh": "不对称迈步姿态；用视线方向、身体弧线和手势完整表达所有性格关键词",
            "en": "an asymmetric mid-step pose that expresses every personality constraint through eye line, body arc, and gesture",
        },
        "lighting": {
            "zh": "冷暖双色轮廓光配柔和正面补光",
            "en": "cool-warm dual rim lights with a soft frontal fill",
        },
    },
)

_PALETTE_OPTIONS = (
    ("#5A47C7", "#FFF4D6", "indigo / cream", "靛蓝 / 奶油"),
    ("#E66B85", "#BEE9FF", "berry / ice blue", "莓红 / 冰蓝"),
    ("#25365C", "#F2B45E", "navy / amber", "海军蓝 / 琥珀"),
    ("#6D7CF6", "#F4F7FF", "periwinkle / pearl", "长春花蓝 / 珍珠白"),
    ("#173E46", "#F7DA66", "deep teal / firefly yellow", "深青 / 萤火黄"),
    ("#FF786F", "#F6F0E8", "coral / warm white", "珊瑚 / 暖白"),
    ("#6D4891", "#DAB8F5", "plum / lilac", "李子紫 / 丁香紫"),
    ("#3D8E89", "#F4B942", "sea teal / yuzu", "海青 / 柚子黄"),
)

_AUTO_PRIMARY = ("#82E6C2", "#F15A8A", "#D88745", "#65C9E8", "#8B6BD6", "#5DC48D")


def _localized(value: dict[str, str], language: str) -> str:
    return value[language]


def _clean_text(value: str, field: str, max_length: int) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        raise ValueError(f"{field} cannot be empty")
    if _CONTROL_CHARACTERS.search(cleaned):
        raise ValueError(f"{field} contains unsupported control characters")
    if len(cleaned) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")
    return cleaned


def normalize_keywords(values: Iterable[str]) -> list[str]:
    """Split, clean, and de-duplicate keyword input while preserving literal wording."""
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        for part in _SPLIT_KEYWORDS.split(value):
            part = " ".join(part.strip().split())
            if not part:
                continue
            part = _clean_text(part, "keyword", 120)
            folded = part.casefold()
            if folded not in seen:
                normalized.append(part)
                seen.add(folded)
    if not normalized:
        raise ValueError("at least one non-empty keyword is required")
    if len(normalized) > 20:
        raise ValueError("at most 20 keywords are supported")
    return normalized


def normalize_likeness_cues(values: Iterable[str]) -> list[str]:
    """Clean optional likeness cues without treating them as inferred attributes."""
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            continue
        cleaned = _clean_text(cleaned, "likeness cue", MAX_LIKENESS_CUE_LENGTH)
        folded = cleaned.casefold()
        if folded not in seen:
            normalized.append(cleaned)
            seen.add(folded)
    if len(normalized) > MAX_LIKENESS_CUES:
        raise ValueError(f"at most {MAX_LIKENESS_CUES} likeness cues are supported")
    return normalized


def _extract_cues(values: Sequence[str], rules: Sequence[tuple[str, Sequence[str]]]) -> list[str]:
    found: list[str] = []
    found_set: set[str] = set()
    for value in values:
        occupied: list[tuple[int, int]] = []
        folded = value.casefold()
        for cue, patterns in rules:
            for pattern in patterns:
                for match in re.finditer(pattern, folded, flags=re.IGNORECASE):
                    span = match.span()
                    if any(span[0] < end and start < span[1] for start, end in occupied):
                        continue
                    occupied.append(span)
                    if cue not in found_set:
                        found.append(cue)
                        found_set.add(cue)
    return found


def detect_color_cues(keywords: Sequence[str]) -> list[str]:
    return _extract_cues(keywords, _COLOR_RULES)


def detect_required_accessories(keywords: Sequence[str]) -> list[str]:
    return _extract_cues(keywords, _ACCESSORY_RULES)


def _resolve_language(requested: str, values: Sequence[str]) -> str:
    if requested not in LANGUAGES:
        raise ValueError(f"language must be one of: {', '.join(LANGUAGES)}")
    if requested != "auto":
        return requested
    return "zh" if any(_CJK.search(value) for value in values) else "en"


def _resolved_seed(seed: str | int | None, canonical_request: str) -> int:
    # Keep serialized seeds exact in both Python and JavaScript JSON consumers.
    js_safe_integer_mask = (1 << 53) - 1
    if seed is None:
        digest = hashlib.sha256(canonical_request.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") & js_safe_integer_mask
    if isinstance(seed, int):
        return seed & js_safe_integer_mask
    cleaned = _clean_text(str(seed), "seed", 128)
    try:
        return int(cleaned, 0) & js_safe_integer_mask
    except ValueError:
        digest = hashlib.sha256(cleaned.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") & js_safe_integer_mask


def _material_for(
    archetype: dict[str, Any], requested: str | None, language: str
) -> tuple[str, str, str]:
    core = requested or _localized(archetype["default_material"], language)
    treatment = _localized(archetype["material_treatment"], language)
    separator = "；" if language == "zh" else "; "
    return core, treatment, f"{core}{separator}{treatment}"


def _likeness_lock(
    source_mode: str, cues: list[str], language: str
) -> dict[str, Any]:
    if language == "zh":
        instructions = {
            "selfie": "以用户明确提供的自拍为相似性参考，只转译可见特征与用户自述特征，不添加未提供的个人属性。",
            "reference": "以用户明确提供的参考图主体为身份参考，只保留可见轮廓、色块、标记和配件关系，不复制背景、文字或水印。",
            "keywords": "不使用人物或外部主体相似性，只依据字面关键词建立原创角色身份。",
        }
        policy = "只保留用户明确给出的提示，不推断敏感属性；若提示与可见参考冲突，先请求用户确认。"
    else:
        instructions = {
            "selfie": "Use only the visible traits in the user-provided selfie and traits the user explicitly states; do not add or infer personal attributes.",
            "reference": "Use the user-provided reference subject for visible silhouette, color blocking, markings, and accessory relationships only; do not copy its background, text, or watermark.",
            "keywords": "Use no personal or external-subject likeness; build an original identity only from the literal keyword constraints.",
        }
        policy = "Preserve only cues the user explicitly supplies, never infer sensitive attributes, and ask before resolving a conflict with the visible reference."
    return {
        "source_mode": source_mode,
        "cues": cues,
        "instruction": instructions[source_mode],
        "cue_policy": policy,
    }


def _accessory_construction(
    accessories: list[str], concept_index: int, language: str
) -> dict[str, Any]:
    if not accessories:
        empty_text = (
            "未识别到必须配件；不要发明会替代字面核心条件的徽章或通用道具"
            if language == "zh"
            else "No required accessory was detected; do not invent a badge or generic prop that replaces a literal core constraint"
        )
        return {
            "required_accessory": [],
            "physically_attached": False,
            "construction": empty_text,
        }
    clauses = [_ACCESSORY_ATTACHMENTS[item][concept_index][language] for item in accessories]
    construction = ("；" if language == "zh" else "; ").join(clauses)
    if language == "en":
        construction = construction[:1].upper() + construction[1:]
    return {
        "required_accessory": accessories,
        "physically_attached": True,
        "construction": construction,
    }


def _palette_for(
    *,
    archetype: dict[str, Any],
    option: tuple[str, str, str, str],
    color_cues: list[str],
    auto_primary: str,
    language: str,
) -> dict[str, Any]:
    required_colors = [
        {"cue": cue, "name": _COLOR_INFO[cue][language], "hex": _COLOR_INFO[cue]["hex"]}
        for cue in color_cues
    ]
    primary = required_colors[0]["hex"] if required_colors else auto_primary
    secondary, accent, complement_en, complement_zh = option
    strategy = _localized(archetype["palette_strategy"], language)
    if language == "zh":
        name = f"{strategy.split('：', 1)[0]} · {complement_zh}"
    else:
        name = f"{strategy.split(':', 1)[0]} · {complement_en}"
    return {
        "name": name,
        "strategy": strategy,
        "required_color_cues": color_cues,
        "required_colors": required_colors,
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "ratios_percent": archetype["ratios"],
    }


def _literal_core_text(keywords: Sequence[str], language: str) -> str:
    quoted = "; ".join(f'"{item}"' for item in keywords)
    if language == "zh":
        return f"字面核心条件（每一项都必须完整保留）：{quoted}"
    return f"Literal core constraints (preserve every item fully and verbatim): {quoted}"


def build_spec(
    keyword_values: Sequence[str],
    *,
    name: str | None = None,
    material: str | None = None,
    seed: str | int | None = None,
    source_mode: str = "keywords",
    likeness_cues: Sequence[str] | None = None,
    language: str = "auto",
) -> dict[str, Any]:
    """Return a reproducible brief whose three concepts preserve every literal constraint."""
    keywords = normalize_keywords(keyword_values)
    clean_name = _clean_text(name, "name", 60) if name is not None else None
    clean_material = _clean_text(material, "material", 80) if material is not None else None
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"source mode must be one of: {', '.join(SOURCE_MODES)}")
    clean_likeness_cues = normalize_likeness_cues(likeness_cues or [])
    resolved_language = _resolve_language(
        language,
        keywords + clean_likeness_cues + ([clean_name] if clean_name else []) + ([clean_material] if clean_material else []),
    )
    color_cues = detect_color_cues(keywords)
    required_accessories = detect_required_accessories(keywords)
    canonical_request = json.dumps(
        {
            "keywords": keywords,
            "language": resolved_language,
            "likeness_cues": clean_likeness_cues,
            "material": clean_material,
            "name": clean_name,
            "source_mode": source_mode,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    numeric_seed = _resolved_seed(seed, canonical_request)
    rng = random.Random(numeric_seed)
    consistency_token = hashlib.sha256(
        f"{canonical_request}|{numeric_seed}".encode("utf-8")
    ).hexdigest()[:12]
    pet_name = clean_name or f"Pet-{consistency_token[:6].upper()}"
    recommendation_digest = hashlib.sha256(f"recommend|{numeric_seed}".encode("utf-8")).digest()
    recommended_concept_id = _ARCHETYPES[
        int.from_bytes(recommendation_digest[:4], "big") % len(_ARCHETYPES)
    ]["id"]
    palette_options = rng.sample(list(_PALETTE_OPTIONS), k=3)
    auto_primaries = rng.sample(list(_AUTO_PRIMARY), k=3)
    likeness_lock = _likeness_lock(source_mode, clean_likeness_cues, resolved_language)
    literal_core_text = _literal_core_text(keywords, resolved_language)

    if resolved_language == "zh":
        must_avoid = [
            "像素画、低分辨率马赛克或像素描边",
            "把任何字面核心条件替换成徽章、手持通用道具或抽象图案",
            "遗漏或替换用户指定颜色、物种、职业、性格、服装或配件",
            "文字、品牌商标、水印和复杂背景",
        ]
        selection_action = "用户选择方案后，把该方案的 candidate_identity 完整复制为最终跨帧身份锁；选择前不要锁定候选头型或五官。"
        semantic_message = "三套候选都必须保留相同的字面语义核心、用户颜色、指定材料和必需配件类别。"
    else:
        must_avoid = [
            "pixel art, low-resolution mosaic rendering, or pixel outlines",
            "replacing any literal core constraint with a badge, hand-held generic prop, or abstract motif",
            "omitting or substituting a requested color, species, role, personality, garment, or accessory",
            "text, brand marks, watermarks, or complex backgrounds",
        ]
        selection_action = "After the user selects a concept, copy that concept's complete candidate_identity into the final cross-frame identity lock; do not lock a candidate head or face before selection."
        semantic_message = "All three candidates must retain the same literal semantic core, user colors, requested material, and required accessory classes."

    semantic_core = {
        "literal_core_constraints": keywords,
        "required_color_cues": color_cues,
        "required_accessory": required_accessories,
        "requested_material": clean_material,
    }
    identity_lock = {
        "status": "pending_selection",
        "pending_selection": True,
        "pet_name": pet_name,
        "consistency_token": consistency_token,
        "semantic_core": semantic_core,
        "likeness_lock": likeness_lock,
        "locked_now": ["semantic_core", "likeness_lock"],
        "not_yet_locked": ["head_geometry", "face_construction", "candidate_identity"],
        "selection_action": selection_action,
        "must_avoid": must_avoid,
    }

    concepts: list[dict[str, Any]] = []
    for index, archetype in enumerate(_ARCHETYPES):
        title = _localized(archetype["title"], resolved_language)
        direction = _localized(archetype["direction"], resolved_language)
        silhouette = _localized(archetype["silhouette"], resolved_language)
        head_geometry = _localized(archetype["head_geometry"], resolved_language)
        face_construction = _localized(archetype["face_construction"], resolved_language)
        limbs = _localized(archetype["proportions"]["limbs"], resolved_language)
        stance = _localized(archetype["proportions"]["stance"], resolved_language)
        pose = _localized(archetype["pose"], resolved_language)
        lighting = _localized(archetype["lighting"], resolved_language)
        material_core, material_treatment, material_value = _material_for(
            archetype, clean_material, resolved_language
        )
        palette = _palette_for(
            archetype=archetype,
            option=palette_options[index],
            color_cues=color_cues,
            auto_primary=auto_primaries[index],
            language=resolved_language,
        )
        accessory = _accessory_construction(
            required_accessories, index, resolved_language
        )
        color_names = ", ".join(
            f"{item['name']} ({item['hex']})" for item in palette["required_colors"]
        )
        accessory_names = ", ".join(
            _ACCESSORY_NAMES[item][resolved_language] for item in required_accessories
        )
        likeness_text = likeness_lock["instruction"]
        if clean_likeness_cues:
            if resolved_language == "zh":
                likeness_text += f" 明确保留：{'、'.join(clean_likeness_cues)}。"
            else:
                likeness_text += f" Explicitly preserve: {', '.join(clean_likeness_cues)}."

        if resolved_language == "zh":
            color_sentence = (
                f"用户必需颜色（全部保留，并以第一项为主色）：{color_names}。调色策略：{palette['strategy']}；"
                f"辅色 {palette['secondary']}，点缀色 {palette['accent']}。"
                if color_cues
                else f"未识别到用户硬性颜色；使用生成主色 {palette['primary']}。调色策略：{palette['strategy']}。"
            )
            accessory_sentence = (
                f"必需配件类别：{accessory_names}。{accessory['construction']}。保持同类配件与身体物理连接，"
                "只改变几何和附着方式，不得手持、遗漏或替换。"
                if required_accessories
                else f"配件：{accessory['construction']}。"
            )
            render_prompt = (
                f"为名为“{pet_name}”的桌面宠物制作完整角色设计图。{literal_core_text}。"
                "把每一项直接落实为可见的物种结构、身份服装、性格行为、颜色、材料或配件；"
                "不得变成徽章、手持通用道具或抽象图案。"
                f"方向：{direction} 剪影：{silhouette}。头型：{head_geometry}。五官构造：{face_construction}。"
                f"比例：头身比 {archetype['proportions']['head_to_body']}，{limbs}，{stance}。"
                f"指定材料核心：{material_core}，三案都不得替换；本案处理：{material_treatment}。"
                f"{color_sentence}{accessory_sentence}相似性约束：{likeness_text}"
                f"姿态：{pose}。灯光：{lighting}。采用高品质 3D Q版渲染，不是像素画；"
                "正交感相机、完整全身、角色居中、轮廓清楚、纯色摄影棚背景、无文字无水印。"
            )
        else:
            color_sentence = (
                f"Required user colors (preserve all, with the first as primary): {color_names}. "
                f"Palette strategy: {palette['strategy']}; secondary {palette['secondary']}; accent {palette['accent']}. "
                if color_cues
                else f"No hard user color was detected; use generated primary {palette['primary']}. Palette strategy: {palette['strategy']}. "
            )
            accessory_sentence = (
                f"Required accessory classes: {accessory_names}. {accessory['construction']}. Keep each class physically attached to the body; "
                "change only its geometry and attachment method, and never hold, omit, or substitute it. "
                if required_accessories
                else f"Accessory: {accessory['construction']}. "
            )
            render_prompt = (
                f"Create a complete character design for a desktop pet named \"{pet_name}\". {literal_core_text}. "
                "Express every item directly through visible species anatomy, role-defining clothing, personality behavior, color, material, or accessory construction; "
                "do not turn any item into a badge, hand-held generic prop, or abstract motif. "
                f"Direction: {direction} Silhouette: {silhouette}. Head geometry: {head_geometry}. "
                f"Face construction: {face_construction}. Proportions: {archetype['proportions']['head_to_body']} head-to-body, "
                f"{limbs}, {stance}. Required material core: {material_core}; all three concepts must retain it. "
                f"This concept's treatment: {material_treatment}. {color_sentence}{accessory_sentence}"
                f"Likeness constraint: {likeness_text} Pose: {pose}. Lighting: {lighting}. "
                "Use a high-quality 3D chibi render, not pixel art: orthographic-feel camera, full body, centered character, "
                "clear silhouette, plain studio background, no text, and no watermark."
            )

        proportions = {
            "head_to_body": archetype["proportions"]["head_to_body"],
            "limbs": limbs,
            "stance": stance,
        }
        candidate_identity = {
            "head_geometry": head_geometry,
            "face_construction": face_construction,
            "silhouette": silhouette,
            "proportions": proportions,
            "palette": palette,
            "material": material_value,
            "accessory_attachment": accessory,
        }
        concepts.append(
            {
                "id": archetype["id"],
                "title": title,
                "direction": direction,
                "literal_core_constraints": keywords,
                "required_color_cues": color_cues,
                "required_accessory": required_accessories,
                "silhouette": silhouette,
                "proportions": proportions,
                "head_geometry": head_geometry,
                "face_construction": face_construction,
                "face": face_construction,
                "material_core": material_core,
                "material_treatment": material_treatment,
                "material": material_value,
                "surface_finish": material_treatment,
                "palette": palette,
                "accessory": accessory,
                "signature_accessory": accessory["construction"],
                "pose": pose,
                "lighting": lighting,
                "candidate_identity": candidate_identity,
                "render_prompt": render_prompt,
                "negative_prompt": must_avoid,
            }
        )

    if resolved_language == "zh":
        creative_strategy = {
            "goal": "先探索三条显著不同但同样忠于字面输入的 3D Q版方向，再选择并锁定一条进入动画生产。",
            "difference_axes": ["剪影", "头身比例", "候选头型", "候选五官", "材料处理", "调色结构", "配件附着方式", "姿态与灯光"],
            "semantic_core_policy": semantic_message,
            "runtime_note": "最终交付是带透明通道的 3D 渲染精灵图，不是实时 3D 模型。",
        }
    else:
        creative_strategy = {
            "goal": "Explore three clearly different 3D chibi directions that are equally faithful to every literal input, then select and lock one for animation production.",
            "difference_axes": ["silhouette", "proportions", "candidate head", "candidate face", "material treatment", "palette structure", "accessory attachment", "pose and lighting"],
            "semantic_core_policy": semantic_message,
            "runtime_note": "The final deliverable is a transparent 3D-rendered sprite atlas, not a real-time 3D model.",
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "recommended_concept_id": recommended_concept_id,
        "request": {
            "keywords": keywords,
            "literal_core_constraints": keywords,
            "required_color_cues": color_cues,
            "required_accessory": required_accessories,
            "source_mode": source_mode,
            "likeness_cues": clean_likeness_cues,
            "language": resolved_language,
            "pet_name": pet_name,
            "requested_material": clean_material or "auto",
            "seed": numeric_seed,
            "consistency_token": consistency_token,
        },
        "creative_strategy": creative_strategy,
        "identity_lock": identity_lock,
        "concepts": concepts,
    }


def render_markdown(spec: dict[str, Any]) -> str:
    request = spec["request"]
    lock = spec["identity_lock"]
    language = request["language"]
    literal_list = "; ".join(f'`{item}`' for item in request["literal_core_constraints"])
    colors = ", ".join(request["required_color_cues"]) or ("无" if language == "zh" else "none")
    accessories = ", ".join(request["required_accessory"]) or ("无" if language == "zh" else "none")
    likeness_cues = ("、" if language == "zh" else ", ").join(request["likeness_cues"])
    if not likeness_cues:
        likeness_cues = "无" if language == "zh" else "none"

    if language == "zh":
        lines = [
            f"# {request['pet_name']} — 3D Q版宠物设计提案",
            "",
            "## 输入",
            "",
            f"- 字面核心条件（全部完整保留）：{literal_list}",
            f"- 必需颜色：{colors}",
            f"- 必需配件类别：{accessories}",
            f"- 来源模式：{request['source_mode']}",
            f"- 相似性提示：{likeness_cues}",
            f"- 指定材料：{request['requested_material']}",
            f"- 可复现种子：`{request['seed']}`",
            f"- 推荐概念：`{spec['recommended_concept_id']}`",
            f"- 一致性标识：`{request['consistency_token']}`",
            "",
            "## 身份锁状态",
            "",
            "- 状态：`pending_selection`",
            "- 当前只锁定：字面语义核心与相似性约束",
            "- 尚未锁定：候选头型、五官构造和候选身份",
            f"- 相似性策略：{lock['likeness_lock']['instruction']}",
            f"- 选择后操作：{lock['selection_action']}",
        ]
    else:
        lines = [
            f"# {request['pet_name']} — 3D Chibi Pet Concepts",
            "",
            "## Request",
            "",
            f"- Literal core constraints (preserve all in full): {literal_list}",
            f"- Required color cues: {colors}",
            f"- Required accessory classes: {accessories}",
            f"- Source mode: {request['source_mode']}",
            f"- Likeness cues: {likeness_cues}",
            f"- Requested material: {request['requested_material']}",
            f"- Reproducible seed: `{request['seed']}`",
            f"- Recommended concept: `{spec['recommended_concept_id']}`",
            f"- Consistency token: `{request['consistency_token']}`",
            "",
            "## Identity lock status",
            "",
            "- Status: `pending_selection`",
            "- Locked now: literal semantic core and likeness constraints only",
            "- Not locked yet: candidate head geometry, face construction, or candidate identity",
            f"- Likeness policy: {lock['likeness_lock']['instruction']}",
            f"- After selection: {lock['selection_action']}",
        ]

    for index, concept in enumerate(spec["concepts"], start=1):
        palette = concept["palette"]
        recommendation = (
            "（推荐）" if language == "zh" else " (recommended)"
        ) if concept["id"] == spec["recommended_concept_id"] else ""
        required = "; ".join(f'`{item}`' for item in concept["literal_core_constraints"])
        if language == "zh":
            lines.extend(
                [
                    "",
                    f"## 概念 {index}：{concept['title']}{recommendation}",
                    "",
                    concept["direction"],
                    "",
                    f"- 字面核心条件（全部完整保留）：{required}",
                    f"- 剪影：{concept['silhouette']}",
                    f"- 头型：{concept['head_geometry']}",
                    f"- 五官构造：{concept['face_construction']}",
                    f"- 比例：头身比 {concept['proportions']['head_to_body']}；{concept['proportions']['limbs']}；{concept['proportions']['stance']}",
                    f"- 材料核心：{concept['material_core']}",
                    f"- 材料处理：{concept['material_treatment']}",
                    f"- 调色策略：{palette['strategy']}",
                    f"- 必需颜色：{', '.join(concept['required_color_cues']) or '无'}；辅色 {palette['secondary']}；点缀 {palette['accent']}",
                    f"- 必需配件：{', '.join(concept['required_accessory']) or '无'}",
                    f"- 物理附着：{concept['accessory']['construction']}",
                    f"- 姿态：{concept['pose']}",
                    "",
                    "### 完整生成提示",
                    "",
                    concept["render_prompt"],
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    f"## Concept {index}: {concept['title']}{recommendation}",
                    "",
                    concept["direction"],
                    "",
                    f"- Literal core constraints (preserve all in full): {required}",
                    f"- Silhouette: {concept['silhouette']}",
                    f"- Head geometry: {concept['head_geometry']}",
                    f"- Face construction: {concept['face_construction']}",
                    f"- Proportions: {concept['proportions']['head_to_body']} head-to-body; {concept['proportions']['limbs']}; {concept['proportions']['stance']}",
                    f"- Material core: {concept['material_core']}",
                    f"- Material treatment: {concept['material_treatment']}",
                    f"- Palette strategy: {palette['strategy']}",
                    f"- Required colors: {', '.join(concept['required_color_cues']) or 'none'}; secondary {palette['secondary']}; accent {palette['accent']}",
                    f"- Required accessories: {', '.join(concept['required_accessory']) or 'none'}",
                    f"- Physical attachment: {concept['accessory']['construction']}",
                    f"- Pose: {concept['pose']}",
                    "",
                    "### Full render prompt",
                    "",
                    concept["render_prompt"],
                ]
            )

    if language == "zh":
        lines.extend(
            [
                "",
                "## 选择后",
                "",
                "把选中方案的 `candidate_identity` 完整复制为最终跨帧身份锁；字面核心条件、必需颜色、材料核心和必需配件不得改变。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## After selection",
                "",
                "Copy the selected concept's complete `candidate_identity` into the final cross-frame identity lock. Do not change any literal core constraint, required color, material core, or required accessory class.",
                "",
            ]
        )
    return "\n".join(lines)


def _write_utf8(path_value: str, content: str) -> None:
    path = Path(path_value).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate three reproducible, constraint-faithful 3D chibi pet concepts."
    )
    parser.add_argument(
        "-k",
        "--keywords",
        action="append",
        required=True,
        metavar="TEXT",
        help="Literal core constraints; repeat the flag or separate items with commas.",
    )
    parser.add_argument("--name", help="Optional pet name.")
    parser.add_argument("--material", help="Optional material core retained by all directions.")
    parser.add_argument("--seed", help="Integer or text seed for reproducible variation.")
    parser.add_argument(
        "--source-mode",
        choices=SOURCE_MODES,
        default="keywords",
        help="Identity source mode (default: keywords).",
    )
    parser.add_argument(
        "--likeness-cue",
        action="append",
        default=[],
        metavar="TEXT",
        help=f"Explicit likeness detail to preserve; repeat up to {MAX_LIKENESS_CUES} times.",
    )
    parser.add_argument(
        "--language",
        choices=LANGUAGES,
        default="auto",
        help="Output language; auto selects Chinese for CJK input and English otherwise.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="both",
        help="Standard-output format (default: both).",
    )
    parser.add_argument("--json-out", metavar="PATH", help="Also write canonical JSON to PATH.")
    parser.add_argument("--markdown-out", metavar="PATH", help="Also write Markdown to PATH.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        spec = build_spec(
            args.keywords,
            name=args.name,
            material=args.material,
            seed=args.seed,
            source_mode=args.source_mode,
            likeness_cues=args.likeness_cue,
            language=args.language,
        )
    except ValueError as exc:
        parser.error(str(exc))

    json_text = json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    markdown_text = render_markdown(spec)
    if args.json_out:
        _write_utf8(args.json_out, json_text)
    if args.markdown_out:
        _write_utf8(args.markdown_out, markdown_text)

    if args.format == "json":
        print(json_text, end="")
    elif args.format == "markdown":
        print(markdown_text, end="")
    else:
        print("--- JSON ---")
        print(json_text, end="")
        print("--- MARKDOWN ---")
        print(markdown_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
