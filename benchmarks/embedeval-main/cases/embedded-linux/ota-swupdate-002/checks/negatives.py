"""Negative tests for ota-swupdate-002 (dual-bank A/B + bootcnt)."""

import re


def _drop_copy_2_group(code: str) -> str:
    """Delete the ``copy-2 = { ... };`` block entirely using brace
    counting — a lazy regex terminates on the first nested ``}``,
    which would leave image entries dangling.
    """
    m = re.search(r"\bcopy-2\s*=\s*\{", code)
    if not m:
        return code
    depth = 1
    i = m.end()
    while i < len(code) and depth:
        c = code[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    # Consume trailing ``;`` and optional newline.
    if i < len(code) and code[i] == ";":
        i += 1
    if i < len(code) and code[i] == "\n":
        i += 1
    return code[: m.start()] + code[i:]


def _rename_copy_2_to_copy_1(code: str) -> str:
    """Both groups become ``copy-1``."""
    return code.replace("copy-2 =", "copy-1 =", 1)


def _same_devices_in_both_groups(code: str) -> str:
    """Collapse all device= values to a shared set."""
    return re.sub(
        r'device\s*=\s*"[^"]+"',
        'device = "/dev/mmcblk0p1"',
        code,
    )


def _drop_bootenv_list(code: str) -> str:
    return re.sub(
        r"bootenv:\s*\([\s\S]*?\)\s*;",
        "",
        code,
        count=1,
    )


def _bootcount_enable_zero(code: str) -> str:
    return re.sub(
        r'(name\s*=\s*"bootcount_enable"\s*;\s*value\s*=\s*)"1"',
        r'\1"0"',
        code,
    )


def _drop_upgrade_available(code: str) -> str:
    """Remove the upgrade_available bootenv entry."""
    return re.sub(
        r",?\s*\{\s*name\s*=\s*\"upgrade_available\"[\s\S]*?\}\s*",
        "",
        code,
        count=1,
    )


def _misspell_upgrade_available(code: str) -> str:
    return code.replace("upgrade_available", "upgraded_available")


def _bootenv_as_dict_not_list(code: str) -> str:
    """Turn ``bootenv: ( { ... } );`` into ``bootenv = { ... };``."""
    return re.sub(
        r"bootenv:\s*\(",
        "bootenv = {",
        code,
        count=1,
    ).replace(");", "};", 2)  # close software } + bootenv } later


def _drop_sha256_in_copy_2(code: str) -> str:
    """Remove sha256 from all entries in the copy-2 group."""
    # Find the copy-2 section and strip its sha256 lines.
    m = re.search(r"copy-2\s*=\s*\{", code)
    if not m:
        return code
    start = m.end()
    depth = 1
    i = start
    while i < len(code) and depth:
        c = code[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    section = code[start : i - 1]
    scrubbed = re.sub(r'^\s*sha256\s*=.*\n', "", section, flags=re.MULTILINE)
    return code[:start] + scrubbed + code[i - 1 :]


def _drop_hw_compat(code: str) -> str:
    return re.sub(
        r'^\s*hardware-compatibility\s*=.*\n',
        "",
        code,
        count=1,
        flags=re.MULTILINE,
    )


def _only_two_images_in_copy_1(code: str) -> str:
    """Drop the third image entry from copy-1 (rootfs)."""
    return re.sub(
        r",\s*\{[^{}]*?rootfs\.a\.ext4[^{}]*?\}",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _bootenv_value_not_string(code: str) -> str:
    """Strip the quotes from bootcount_enable value — libconfig accepts
    bare ints but SWUpdate expects strings for U-Boot env vars."""
    return re.sub(
        r'(name\s*=\s*"bootcount_enable"\s*;\s*value\s*=\s*)"1"',
        r"\g<1>1",
        code,
    )


def _yamlify_top(code: str) -> str:
    return "---\nsoftware:\n" + code


NEGATIVES = [
    {
        "name": "drop_copy_2_group",
        "description": "Delete copy-2 selection group. Single-bank update — failback impossible because there's no ``previous-known-good`` partition set.",
        "mutation": _drop_copy_2_group,
        "must_fail": [
            "two_selection_groups_copy_1_copy_2",
            "copy_2_has_three_images",
            "copy_2_group_keyword",
        ],
        "factor_id": "E4.1",
    },
    {
        "name": "rename_copy_2_to_copy_1",
        "description": "Rename copy-2 → copy-1. Two groups named identically; SWUpdate's last-wins semantics leave only one bank configured.",
        "mutation": _rename_copy_2_to_copy_1,
        "must_fail": [
            "two_selection_groups_copy_1_copy_2",
            "copy_2_group_keyword",
        ],
        "factor_id": "E4.1",
    },
    {
        "name": "same_devices_in_both_groups",
        "description": "Collapse device= to a shared path across groups. Installer writes both banks to the same partition — no A/B.",
        "mutation": _same_devices_in_both_groups,
        "must_fail": ["selection_groups_have_distinct_devices"],
        "factor_id": "E4.1",
    },
    {
        "name": "drop_bootenv_list",
        "description": "Remove bootenv list. U-Boot receives no notification that an update is pending — bootcnt mechanism never arms.",
        "mutation": _drop_bootenv_list,
        "must_fail": [
            "bootenv_list_present",
            "bootcount_enable_set_to_1",
            "upgrade_available_set_to_1",
            "bootenv_keyword_present",
        ],
        "factor_id": "E4.2",
    },
    {
        "name": "bootcount_enable_zero",
        "description": "Set bootcount_enable=0 — bootcnt mechanism disabled, so a bricked new bank never triggers failback.",
        "mutation": _bootcount_enable_zero,
        "must_fail": ["bootcount_enable_set_to_1"],
        "factor_id": "E4.2",
    },
    {
        "name": "drop_upgrade_available",
        "description": "Remove upgrade_available entry. Bootloader cannot distinguish normal boot from post-update boot; no failback trigger.",
        "mutation": _drop_upgrade_available,
        "must_fail": ["upgrade_available_set_to_1"],
        "factor_id": "E4.2",
    },
    {
        "name": "misspell_upgrade_available",
        "description": "Typo upgrade_available → upgraded_available. U-Boot looks up the literal variable name; typo means no signal received.",
        "mutation": _misspell_upgrade_available,
        "must_fail": ["upgrade_available_set_to_1"],
        "factor_id": "F1.1",
    },
    {
        "name": "bootenv_as_dict_not_list",
        "description": "Swap bootenv: ( ... ); list form for bootenv = { ... }; dict form. Entries no longer iterate.",
        "mutation": _bootenv_as_dict_not_list,
        "must_fail": [
            "bootenv_list_present",
            "bootcount_enable_set_to_1",
            "upgrade_available_set_to_1",
        ],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_sha256_in_copy_2",
        "description": "Strip sha256 from copy-2's image entries. B-bank update writes unverified bytes.",
        "mutation": _drop_sha256_in_copy_2,
        "must_fail": ["all_image_entries_have_sha256"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_hw_compatibility",
        "description": "Remove hardware-compatibility. Installer proceeds on incompatible revisions.",
        "mutation": _drop_hw_compat,
        "must_fail": [
            "hardware_compatibility_list_nonempty",
            "hardware_compatibility_keyword_present",
        ],
        "factor_id": "E6.1",
    },
    {
        "name": "only_two_images_in_copy_1",
        "description": "Drop the third image from copy-1. A-bank is incomplete; failback targets a broken image set.",
        "mutation": _only_two_images_in_copy_1,
        "must_fail": ["copy_1_has_three_images"],
        "factor_id": "F6.2",
    },
    {
        "name": "bootenv_value_not_string",
        "description": "Strip quotes from bootcount_enable value. libconfig accepts bare 1; U-Boot env expects string form.",
        "mutation": _bootenv_value_not_string,
        "must_fail": ["bootcount_enable_set_to_1"],
        "factor_id": "F6.2",
    },
    {
        "name": "yamlify_top",
        "description": "Prepend YAML header; content is now parsed as YAML not libconfig.",
        "mutation": _yamlify_top,
        "must_fail": ["no_yaml_syntax"],
        "factor_id": "F6.1",
    },
]
