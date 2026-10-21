"""Behavioral checks for ota-swupdate-002 (dual-bank A/B + bootcnt)."""

import re

from embedeval.check_utils import (
    libconfig_list_body,
    libconfig_list_entries,
    libconfig_section_body,
    strip_systemd_comments,
    swupdate_hardware_compatibility_list,
)
from embedeval.models import CheckDetail


def _images_list_body_in_section(section_body: str) -> str | None:
    """Within a libconfig section body, return the ``images: ( ... )`` body."""
    m = re.search(r"images\s*:\s*\(", section_body)
    if not m:
        return None
    depth = 1
    start = m.end()
    i = start
    while i < len(section_body) and depth:
        c = section_body[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    if depth:
        return None
    return section_body[start : i - 1]


def _devices_in_group(text: str, group_path: str) -> list[str]:
    body = libconfig_section_body(text, group_path)
    if body is None:
        return []
    images_body = _images_list_body_in_section(body)
    if images_body is None:
        return []
    devs: list[str] = []
    for entry in libconfig_list_entries(images_body):
        dm = re.search(r'device\s*=\s*"([^"]+)"', entry)
        if dm:
            devs.append(dm.group(1))
    return devs


def _bootenv_entries(text: str) -> list[tuple[str, str]]:
    body = libconfig_list_body(text, "bootenv")
    if body is None:
        return []
    out: list[tuple[str, str]] = []
    for entry in libconfig_list_entries(body):
        nm = re.search(r'name\s*=\s*"([^"]+)"', entry)
        vm = re.search(r'value\s*=\s*"([^"]+)"', entry)
        if nm and vm:
            out.append((nm.group(1), vm.group(1)))
    return out


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. hardware-compatibility non-empty.
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

    # 2. Two selection groups named copy-1 and copy-2 present.
    copy1_body = libconfig_section_body(generated_code, "copy-1")
    copy2_body = libconfig_section_body(generated_code, "copy-2")
    details.append(
        CheckDetail(
            check_name="two_selection_groups_copy_1_copy_2",
            passed=copy1_body is not None and copy2_body is not None,
            expected="both copy-1 { ... } and copy-2 { ... } selection groups",
            actual=f"copy-1={'present' if copy1_body else 'missing'}, "
            f"copy-2={'present' if copy2_body else 'missing'}",
            check_type="constraint",
        )
    )

    # 3. Each group has three images.
    g1_devs = _devices_in_group(generated_code, "copy-1")
    g2_devs = _devices_in_group(generated_code, "copy-2")
    details.append(
        CheckDetail(
            check_name="copy_1_has_three_images",
            passed=len(g1_devs) == 3,
            expected="copy-1 declares 3 image entries with device=",
            actual=f"{len(g1_devs)} device entries",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="copy_2_has_three_images",
            passed=len(g2_devs) == 3,
            expected="copy-2 declares 3 image entries with device=",
            actual=f"{len(g2_devs)} device entries",
            check_type="constraint",
        )
    )

    # 4. Distinct device paths ACROSS the two groups (at least the
    # kernel and rootfs partitions must be on different block devices).
    # Bootloader image (eMMC boot0/boot1) may legitimately share the
    # filename but must differ by block device.
    all_devs = g1_devs + g2_devs
    unique_ratio = len(set(all_devs)) / max(1, len(all_devs))
    details.append(
        CheckDetail(
            check_name="selection_groups_have_distinct_devices",
            passed=len(set(all_devs)) == len(all_devs) and len(all_devs) == 6,
            expected="all 6 device= values across the two groups are distinct",
            actual=f"{len(set(all_devs))} unique of {len(all_devs)} "
            f"(ratio={unique_ratio:.2f})",
            check_type="constraint",
        )
    )

    # 5-6. bootenv list present with the two required entries.
    env = _bootenv_entries(generated_code)
    env_names = {n for n, _ in env}
    env_map = dict(env)
    details.append(
        CheckDetail(
            check_name="bootenv_list_present",
            passed=libconfig_list_body(generated_code, "bootenv") is not None,
            expected='"bootenv: ( ... );" list declared at software level',
            actual=f"{len(env)} entries parsed",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="bootcount_enable_set_to_1",
            passed=env_map.get("bootcount_enable") == "1",
            expected='bootenv entry name="bootcount_enable" value="1"',
            actual=f"bootcount_enable={env_map.get('bootcount_enable')!r}",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="upgrade_available_set_to_1",
            passed=env_map.get("upgrade_available") == "1",
            expected='bootenv entry name="upgrade_available" value="1"',
            actual=f"upgrade_available={env_map.get('upgrade_available')!r}",
            check_type="constraint",
        )
    )

    # 6b. Every image entry in every group carries sha256 — protects
    # against silently dropping the integrity check in just one bank.
    def _sha_ok_for(group: str) -> bool:
        body = libconfig_section_body(generated_code, group)
        if body is None:
            return False
        images_body = _images_list_body_in_section(body)
        if images_body is None:
            return False
        entries = libconfig_list_entries(images_body)
        if not entries:
            return False
        return all(re.search(r"\bsha256\s*=", e) for e in entries)

    details.append(
        CheckDetail(
            check_name="all_image_entries_have_sha256",
            passed=_sha_ok_for("copy-1") and _sha_ok_for("copy-2"),
            expected="every image entry in copy-1 AND copy-2 has sha256=",
            actual=f"copy-1 ok={_sha_ok_for('copy-1')}, "
            f"copy-2 ok={_sha_ok_for('copy-2')}",
            check_type="constraint",
        )
    )

    # 7. Each bootenv entry has both name and value.
    env_well_formed = all(n and v for n, v in env)
    details.append(
        CheckDetail(
            check_name="bootenv_entries_well_formed",
            passed=env_well_formed and len(env) >= 2,
            expected="≥2 bootenv entries, each with name= and value=",
            actual=f"entries={env}",
            check_type="constraint",
        )
    )

    # 8. No single selection group (guard against the LLM collapsing
    # both to a single "copy-1" group).
    has_single_only = copy1_body is not None and copy2_body is None
    details.append(
        CheckDetail(
            check_name="no_single_selection_group",
            passed=not has_single_only,
            expected="both copy-1 and copy-2 groups (not a single-group layout)",
            actual=f"copy-1 only? {has_single_only}",
            check_type="constraint",
        )
    )

    # 9. No YAML top-level.
    stripped = strip_systemd_comments(generated_code)
    yaml_head = bool(
        re.search(r"^\s*---\s*$|^\s*software\s*:\s*$", stripped, re.MULTILINE)
    )
    details.append(
        CheckDetail(
            check_name="no_yaml_syntax",
            passed=not yaml_head,
            expected="no YAML top-level marker",
            actual="detected" if yaml_head else "clean",
            check_type="constraint",
        )
    )

    return details
