"""Behavioral checks for ota-swupdate-001 (SWUpdate minimal triple).

Asserts the grammar-level discriminators that distinguish a valid
libconfig sw-description from YAML/JSON drift and from incomplete
image entries. All scoped_contains calls pass ``scope='raw'``.
"""

import re

from embedeval.check_utils import (
    libconfig_list_body,
    libconfig_list_entries,
    scoped_contains,
    strip_systemd_comments,
    swupdate_hardware_compatibility_list,
    swupdate_images_has_sha256,
    swupdate_libconfig_has,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. ``software = { ... };`` top-level block (libconfig, not YAML/JSON).
    has_software_block = bool(
        re.search(
            r"\bsoftware\s*=\s*\{",
            strip_systemd_comments(generated_code),
            re.MULTILINE,
        )
    )
    details.append(
        CheckDetail(
            check_name="software_block_top_level",
            passed=has_software_block,
            expected='"software = { ... };" libconfig top-level block',
            actual="present" if has_software_block else "missing",
            check_type="constraint",
        )
    )

    # 2. version = "..." inside software (semver-ish).
    version = swupdate_libconfig_has(generated_code, "software", "version")
    version_ok = bool(version) and re.match(r"^\d+\.\d+(\.\d+)?", version.strip())
    details.append(
        CheckDetail(
            check_name="version_field_present",
            passed=bool(version_ok),
            expected='version = "X.Y[.Z]" inside software block',
            actual=f"version={version!r}" if version else "missing",
            check_type="constraint",
        )
    )

    # 3. hardware-compatibility = [ ... ] non-empty.
    hw = swupdate_hardware_compatibility_list(generated_code)
    details.append(
        CheckDetail(
            check_name="hardware_compatibility_list_nonempty",
            passed=len(hw) >= 1,
            expected="hardware-compatibility = [ ... ] with ≥1 entry",
            actual=f"list={hw}",
            check_type="constraint",
        )
    )

    # 4. images: ( ... ) list present.
    images_body = libconfig_list_body(generated_code, "images")
    has_images = images_body is not None
    details.append(
        CheckDetail(
            check_name="images_list_present",
            passed=has_images,
            expected='"images: ( ... );" list declared',
            actual="present" if has_images else "missing",
            check_type="constraint",
        )
    )

    # 5-7. Each image entry has filename/device/sha256.
    entries = libconfig_list_entries(images_body) if images_body else []

    def _all_have(key: str) -> bool:
        if not entries:
            return False
        pat = re.compile(rf"\b{re.escape(key)}\s*=", re.MULTILINE)
        return all(pat.search(e) for e in entries)

    details.append(
        CheckDetail(
            check_name="each_image_has_filename",
            passed=_all_have("filename"),
            expected="every images entry has filename =",
            actual=f"{len(entries)} image entries parsed",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="each_image_has_device",
            passed=_all_have("device"),
            expected="every images entry has device =",
            actual=f"{len(entries)} image entries parsed",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="each_image_has_sha256",
            passed=swupdate_images_has_sha256(generated_code),
            expected="every images entry has sha256 =",
            actual=f"{len(entries)} image entries parsed",
            check_type="constraint",
        )
    )

    # 8. Three images declared.
    details.append(
        CheckDetail(
            check_name="three_images_declared",
            passed=len(entries) == 3,
            expected="exactly 3 image entries",
            actual=f"{len(entries)} image entries",
            check_type="constraint",
        )
    )

    # 9. Distinct device paths across the three images.
    devices: list[str] = []
    for e in entries:
        dm = re.search(r'device\s*=\s*"([^"]+)"', e)
        if dm:
            devices.append(dm.group(1))
    distinct_ok = len(devices) == len(set(devices)) and len(devices) == len(entries)
    details.append(
        CheckDetail(
            check_name="distinct_device_paths",
            passed=distinct_ok,
            expected="all image entries have distinct device paths",
            actual=f"devices={devices}",
            check_type="constraint",
        )
    )

    # 10. No YAML syntax (top-level "---" or "software:" without brace).
    stripped = strip_systemd_comments(generated_code)
    yaml_head = bool(re.search(r"^\s*---\s*$", stripped, re.MULTILINE))
    yaml_sw = bool(
        re.search(r"^\s*software\s*:\s*$", stripped, re.MULTILINE)
    )
    details.append(
        CheckDetail(
            check_name="no_yaml_syntax",
            passed=not (yaml_head or yaml_sw),
            expected="no YAML '---' marker and no 'software:' (YAML form)",
            actual=f"yaml_head={yaml_head}, yaml_section={yaml_sw}",
            check_type="constraint",
        )
    )

    # 11. No JSON syntax (top-level {"software":).
    json_start = scoped_contains(generated_code, '{"software"', scope="raw")
    details.append(
        CheckDetail(
            check_name="no_json_syntax",
            passed=not json_start,
            expected="no JSON '{\"software\":' top-level form",
            actual="detected" if json_start else "clean",
            check_type="constraint",
        )
    )

    return details
