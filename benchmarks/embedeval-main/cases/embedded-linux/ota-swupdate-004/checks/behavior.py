"""Behavioral checks for ota-swupdate-004 (scripts + lifecycle)."""

import re

from embedeval.check_utils import (
    libconfig_list_body,
    libconfig_list_entries,
    swupdate_hardware_compatibility_list,
)
from embedeval.models import CheckDetail

_ALLOWED_SCRIPT_TYPES = {
    "preinstall",
    "postinstall",
    "shellscript",
    "lua",
    "swupdate",
}


def _script_entries(text: str) -> list[dict[str, str]]:
    body = libconfig_list_body(text, "scripts")
    if body is None:
        return []
    out: list[dict[str, str]] = []
    for entry in libconfig_list_entries(body):
        fn = re.search(r'filename\s*=\s*"([^"]+)"', entry)
        tp = re.search(r'type\s*=\s*"([^"]+)"', entry)
        sh = re.search(r'sha256\s*=\s*"([^"]+)"', entry)
        out.append(
            {
                "filename": fn.group(1) if fn else "",
                "type": tp.group(1) if tp else "",
                "sha256": sh.group(1) if sh else "",
            }
        )
    return out


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. hw-compat non-empty.
    hw = swupdate_hardware_compatibility_list(generated_code)
    details.append(
        CheckDetail(
            check_name="hardware_compatibility_list_nonempty",
            passed=len(hw) >= 1,
            expected="hardware-compatibility non-empty",
            actual=f"{hw}",
            check_type="constraint",
        )
    )

    # 2. scripts list present.
    scripts_body = libconfig_list_body(generated_code, "scripts")
    details.append(
        CheckDetail(
            check_name="scripts_list_present",
            passed=scripts_body is not None,
            expected='"scripts: ( ... );" list declared',
            actual="present" if scripts_body else "missing",
            check_type="constraint",
        )
    )

    entries = _script_entries(generated_code)

    # 3. Exactly two script entries.
    details.append(
        CheckDetail(
            check_name="two_script_entries",
            passed=len(entries) == 2,
            expected="exactly 2 script entries",
            actual=f"{len(entries)} entries",
            check_type="constraint",
        )
    )

    # 4. Every entry has filename / type / sha256.
    has_filename = all(e["filename"] for e in entries) and bool(entries)
    has_type = all(e["type"] for e in entries) and bool(entries)
    has_sha = all(e["sha256"] for e in entries) and bool(entries)
    details.append(
        CheckDetail(
            check_name="each_script_has_filename",
            passed=has_filename,
            expected="every script entry has filename=",
            actual=f"{entries}",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="each_script_has_type",
            passed=has_type,
            expected="every script entry has type=",
            actual=f"{entries}",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="each_script_has_sha256",
            passed=has_sha,
            expected="every script entry has sha256=",
            actual=f"{entries}",
            check_type="constraint",
        )
    )

    # 5. All types from allowed set.
    bad_types = [e["type"] for e in entries if e["type"] not in _ALLOWED_SCRIPT_TYPES]
    details.append(
        CheckDetail(
            check_name="script_types_from_allowed_set",
            passed=not bad_types and bool(entries),
            expected=f"all script types in {sorted(_ALLOWED_SCRIPT_TYPES)}",
            actual=f"unknown types={bad_types}",
            check_type="constraint",
        )
    )

    # 6. At least one preinstall type.
    has_pre = any(e["type"] == "preinstall" for e in entries)
    details.append(
        CheckDetail(
            check_name="has_preinstall_script",
            passed=has_pre,
            expected="at least one preinstall script entry",
            actual=f"types={[e['type'] for e in entries]}",
            check_type="constraint",
        )
    )

    # 7. At least one postinstall OR lua OR swupdate type (post-image work).
    has_post = any(
        e["type"] in {"postinstall", "lua", "swupdate"} for e in entries
    )
    details.append(
        CheckDetail(
            check_name="has_postinstall_or_lua_script",
            passed=has_post,
            expected="at least one postinstall / lua / swupdate script",
            actual=f"types={[e['type'] for e in entries]}",
            check_type="constraint",
        )
    )

    # 8. Distinct filenames.
    names = [e["filename"] for e in entries]
    distinct = len(set(names)) == len(names) and bool(names)
    details.append(
        CheckDetail(
            check_name="distinct_script_filenames",
            passed=distinct,
            expected="script filenames are distinct",
            actual=f"names={names}",
            check_type="constraint",
        )
    )

    # 9. No inline shell commands leaked into description (idempotency
    # red flag: a prompt-breaking LLM sometimes stuffs ``rm -rf`` there).
    desc_region = re.search(
        r'description\s*=\s*"([^"]*)"', generated_code
    )
    desc_text = desc_region.group(1) if desc_region else ""
    shell_smells = re.search(
        r"\b(?:rm\s+-rf|mkfs\.|dd\s+if=|>>\s*/|>\s*/dev/)",
        desc_text,
    )
    details.append(
        CheckDetail(
            check_name="no_inline_shell_in_description",
            passed=shell_smells is None,
            expected="no shell commands embedded in description=",
            actual=f"description excerpt={desc_text[:80]!r}",
            check_type="constraint",
        )
    )

    # 10. At least one image entry declared (sanity — TC 004 still
    # installs images even though focus is scripts).
    images_body = libconfig_list_body(generated_code, "images")
    image_entries = (
        libconfig_list_entries(images_body) if images_body else []
    )
    details.append(
        CheckDetail(
            check_name="at_least_one_image",
            passed=len(image_entries) >= 1,
            expected="≥1 image entry",
            actual=f"{len(image_entries)}",
            check_type="constraint",
        )
    )

    return details
