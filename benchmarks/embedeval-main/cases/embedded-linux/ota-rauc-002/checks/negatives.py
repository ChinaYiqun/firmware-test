"""Negative tests for ota-rauc-002 (A/B slot + hook)."""

import re


def _drop_slot_1(code: str) -> str:
    """Remove the [image.rootfs.1] section entirely, whether or not
    another section follows (``|\\Z`` handles last-section placement).
    """
    return re.sub(
        r"\[image\.rootfs\.1\][\s\S]*?(?=\n\s*\[|\Z)",
        "",
        code,
        count=1,
    )


def _letter_index_slots(code: str) -> str:
    """Rename numeric indices 0/1 to letters a/b — looks natural but RAUC
    requires integer indices."""
    code = code.replace("[image.rootfs.0]", "[image.rootfs.a]")
    code = code.replace("[image.rootfs.1]", "[image.rootfs.b]")
    return code


def _same_filename_both_slots(code: str) -> str:
    return code.replace("rootfs-0.ext4", "rootfs.ext4").replace(
        "rootfs-1.ext4", "rootfs.ext4"
    )


def _same_sha256_both_slots(code: str) -> str:
    """Collapse every sha256 value to the first-encountered one — works
    regardless of the actual hex characters (robust to reference drift).
    """
    values = re.findall(r"sha256=([0-9a-fA-F]{64})", code)
    if not values:
        return code
    target = values[0]
    return re.sub(r"sha256=[0-9a-fA-F]{64}", f"sha256={target}", code)


def _drop_hooks_section(code: str) -> str:
    return re.sub(
        r"\[hooks\][\s\S]*?(?=\n\s*\[|\Z)",
        "",
        code,
        count=1,
    )


def _drop_hooks_filename(code: str) -> str:
    """Keep [hooks] header but drop its filename."""
    return re.sub(
        r"(\[hooks\]\s*\n)filename=.*\n",
        r"\1",
        code,
    )


def _strip_key_from_section(code: str, section: str, key: str) -> str:
    """Drop a given ``key=...`` line from the bounded section body.

    Order-independent: finds the section header, walks to the next
    ``\\n[`` or end-of-string, removes the key line from within that
    window. Needed so mutations work when an LLM reorders directives
    within a section (CLAUDE.md 2026-04-19).
    """
    m = re.search(rf"\[{re.escape(section)}\]", code)
    if not m:
        return code
    # Next header boundary OR end-of-string.
    tail = code[m.end() :]
    nh = re.search(r"\n\s*\[", tail)
    rel_end = nh.start() if nh else len(tail)
    body = tail[:rel_end]
    # Allow missing trailing newline when the key is the last line in the
    # section body (which happens when we bound at ``\n[nextheader]`` —
    # the preceding ``\n`` is absorbed into the bound).
    stripped = re.sub(
        rf"^\s*{re.escape(key)}=[^\n]*(?:\n|$)",
        "",
        body,
        flags=re.MULTILINE,
    )
    return code[: m.end()] + stripped + tail[rel_end:]


def _drop_sha256_on_slot_0(code: str) -> str:
    return _strip_key_from_section(code, "image.rootfs.0", "sha256")


def _drop_size_on_slot_1(code: str) -> str:
    return _strip_key_from_section(code, "image.rootfs.1", "size")


def _collapse_both_slots_into_one(code: str) -> str:
    """Keep only a single [image.rootfs] slot — A/B collapses to single."""
    return re.sub(
        r"\[image\.rootfs\.0\]([\s\S]*?)(?=\n\[image\.rootfs\.1\])",
        r"[image.rootfs]\1",
        code,
    ).replace("[image.rootfs.1]", "").strip() + "\n"


def _flatten_slot_0_to_flat_rootfs(code: str) -> str:
    """Drop the image. prefix on slot 0."""
    return code.replace("[image.rootfs.0]", "[rootfs.0]")


def _add_inplace_directive(code: str) -> str:
    """Inject ``inplace=true`` into slot 0 — hallucinated option."""
    return code.replace(
        "[image.rootfs.0]",
        "[image.rootfs.0]\ninplace=true",
    )


def _drop_bundle_format(code: str) -> str:
    return re.sub(r"^\s*format=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_update_compatible(code: str) -> str:
    return re.sub(r"^\s*compatible=.*\n", "", code, count=1, flags=re.MULTILINE)


NEGATIVES = [
    {
        "name": "drop_slot_1",
        "description": "Delete [image.rootfs.1]. No B-slot means no atomic A/B switchover — a failed install loses the known-good copy.",
        "mutation": _drop_slot_1,
        "must_fail": [
            "two_rootfs_slots_declared",
            "no_single_slot_collapse",
            "slot_filenames_distinct",
            "slot_sha256_distinct",
        ],
        "factor_id": "E4.1",
    },
    {
        "name": "letter_index_slots",
        "description": "Rename indices 0/1 → a/b. RAUC requires numeric indices — letters fail the class/index parser.",
        "mutation": _letter_index_slots,
        "must_fail": [
            "two_rootfs_slots_declared",
            "slot_class_uses_numeric_index",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "same_filename_both_slots",
        "description": "Both slots' filename= point to the same bundled image. Install writes identical bytes to both banks — A/B distinction collapses.",
        "mutation": _same_filename_both_slots,
        "must_fail": ["slot_filenames_distinct"],
        "factor_id": "E4.1",
    },
    {
        "name": "same_sha256_both_slots",
        "description": "Both slots' sha256= identical. Same bytes in both banks; atomic switchover is a no-op.",
        "mutation": _same_sha256_both_slots,
        "must_fail": ["slot_sha256_distinct"],
        "factor_id": "E4.1",
    },
    {
        "name": "drop_hooks_section",
        "description": "Remove [hooks] section. Install-check script never runs — signature verification class of checks is skipped.",
        "mutation": _drop_hooks_section,
        "must_fail": ["hooks_has_filename", "hooks_section_header"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_hooks_filename",
        "description": "Keep [hooks] header but remove its filename=. RAUC has no hook registered.",
        "mutation": _drop_hooks_filename,
        "must_fail": ["hooks_has_filename"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_sha256_on_slot_0",
        "description": "Remove sha256 from slot 0. Writing slot 0 skips integrity verification.",
        "mutation": _drop_sha256_on_slot_0,
        "must_fail": ["every_slot_has_sha256"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_size_on_slot_1",
        "description": "Remove size= from slot 1. RAUC cannot size-check the bundled image.",
        "mutation": _drop_size_on_slot_1,
        "must_fail": ["every_slot_has_size"],
        "factor_id": "F6.2",
    },
    {
        "name": "collapse_both_slots_into_one",
        "description": "Merge both slots into a single [image.rootfs] section. A/B layout collapses to single-slot — no atomic switchover possible.",
        "mutation": _collapse_both_slots_into_one,
        "must_fail": ["two_rootfs_slots_declared", "no_single_slot_collapse"],
        "factor_id": "E4.1",
    },
    {
        "name": "flatten_slot_0_to_flat_rootfs",
        "description": "Rename [image.rootfs.0] → [rootfs.0] (drops image. prefix). RAUC stops recognising this as an image slot.",
        "mutation": _flatten_slot_0_to_flat_rootfs,
        "must_fail": ["two_rootfs_slots_declared"],
        "factor_id": "F6.1",
    },
    {
        "name": "add_inplace_directive",
        "description": "Inject ``inplace=true`` into slot 0. Hallucinated option — RAUC does not support in-place writes; parser may reject or ignore silently, either way A/B semantics are wrong.",
        "mutation": _add_inplace_directive,
        "must_fail": ["no_inplace_directive"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_bundle_format",
        "description": "Remove format= from [bundle]. RAUC cannot decide how to process the bundle payload.",
        "mutation": _drop_bundle_format,
        "must_fail": ["bundle_format_valid", "format_directive_present"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_update_compatible",
        "description": "Remove compatible= from [update]. RAUC refuses to install with no device pin.",
        "mutation": _drop_update_compatible,
        "must_fail": ["update_has_compatible", "compatible_directive_present"],
        "factor_id": "E6.1",
    },
]
