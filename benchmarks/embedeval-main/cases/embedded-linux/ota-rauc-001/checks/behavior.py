"""Behavioral checks for ota-rauc-001 (minimal RAUC manifest)."""

import re

from embedeval.check_utils import (
    rauc_image_slots,
    rauc_manifest_section_has,
    strip_systemd_comments,
)
from embedeval.models import CheckDetail

_ALLOWED_BUNDLE_FORMATS = {"plain", "verity", "crypt"}


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. [update] section with compatible + version + description.
    compatible = rauc_manifest_section_has(generated_code, "update", "compatible")
    details.append(
        CheckDetail(
            check_name="update_has_compatible",
            passed=bool(compatible),
            expected='[update] compatible=<vendor,product>',
            actual=f"{compatible!r}" if compatible else "missing",
            check_type="constraint",
        )
    )
    # 1b. compatible should follow the "vendor,product" convention.
    compat_comma = bool(compatible and "," in compatible)
    details.append(
        CheckDetail(
            check_name="compatible_uses_vendor_comma_product_convention",
            passed=compat_comma,
            expected='compatible value contains a comma (vendor,product)',
            actual=f"{compatible!r}",
            check_type="constraint",
        )
    )

    version = rauc_manifest_section_has(generated_code, "update", "version")
    details.append(
        CheckDetail(
            check_name="update_has_version",
            passed=bool(version),
            expected="[update] version=<semver>",
            actual=f"{version!r}" if version else "missing",
            check_type="constraint",
        )
    )
    desc = rauc_manifest_section_has(generated_code, "update", "description")
    details.append(
        CheckDetail(
            check_name="update_has_description",
            passed=bool(desc),
            expected="[update] description=<string>",
            actual=f"{desc!r}" if desc else "missing",
            check_type="constraint",
        )
    )

    # 2. [bundle] section with format= in {plain, verity, crypt}.
    fmt = rauc_manifest_section_has(generated_code, "bundle", "format")
    details.append(
        CheckDetail(
            check_name="bundle_has_format",
            passed=bool(fmt),
            expected="[bundle] format=<plain|verity|crypt>",
            actual=f"{fmt!r}" if fmt else "missing",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="format_value_in_allowed_set",
            passed=bool(fmt) and fmt in _ALLOWED_BUNDLE_FORMATS,
            expected=f"format in {sorted(_ALLOWED_BUNDLE_FORMATS)}",
            actual=f"format={fmt!r}",
            check_type="constraint",
        )
    )

    # 3. Slot sections use [image.<slot>] prefix, not flat [slot].
    slots = rauc_image_slots(generated_code)
    details.append(
        CheckDetail(
            check_name="image_slot_section_present",
            passed=len(slots) >= 1,
            expected="at least one [image.<slot>] section",
            actual=f"slots={slots}",
            check_type="constraint",
        )
    )

    # 3b. Reject a flat [rootfs] section (missing ``image.`` prefix).
    stripped = strip_systemd_comments(generated_code)
    flat_rootfs = bool(re.search(r"^\s*\[rootfs\]\s*$", stripped, re.MULTILINE))
    flat_images_dot = bool(
        re.search(r"^\s*\[images\.rootfs\]\s*$", stripped, re.MULTILINE)
    )
    details.append(
        CheckDetail(
            check_name="image_slot_uses_image_prefix",
            passed=not (flat_rootfs or flat_images_dot),
            expected="slot sections use [image.<slot>] (not [rootfs] or [images.rootfs])",
            actual=f"flat_rootfs={flat_rootfs}, plural_images={flat_images_dot}",
            check_type="constraint",
        )
    )

    # 4. The image.rootfs slot has filename + sha256 + size.
    fn = rauc_manifest_section_has(generated_code, "image.rootfs", "filename")
    sha = rauc_manifest_section_has(generated_code, "image.rootfs", "sha256")
    size = rauc_manifest_section_has(generated_code, "image.rootfs", "size")
    details.append(
        CheckDetail(
            check_name="image_slot_has_filename",
            passed=bool(fn),
            expected="[image.rootfs] filename=<name>",
            actual=f"{fn!r}" if fn else "missing",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="image_slot_has_sha256",
            passed=bool(sha),
            expected="[image.rootfs] sha256=<digest>",
            actual=f"{sha!r}" if sha else "missing",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="image_slot_has_size",
            passed=bool(size) and size.isdigit(),
            expected="[image.rootfs] size=<positive integer bytes>",
            actual=f"{size!r}",
            check_type="constraint",
        )
    )

    # 5. No non-INI grammar (YAML '---', TOML '[[...]]', libconfig '{').
    has_yaml = bool(re.search(r"^\s*---\s*$", stripped, re.MULTILINE))
    # libconfig assignment is ``<key> = { ... }`` at the START of a line.
    # Anchoring to line-start + an identifier prefix avoids false positives
    # on prose values like ``description=Test = { A/B } update`` which are
    # valid INI.
    has_libconfig = bool(
        re.search(r"^\s*\w[\w-]*\s*=\s*\{", stripped, re.MULTILINE)
    )
    has_toml_table_array = bool(re.search(r"^\s*\[\[", stripped, re.MULTILINE))
    details.append(
        CheckDetail(
            check_name="no_non_ini_grammar",
            passed=not (has_yaml or has_libconfig or has_toml_table_array),
            expected="no YAML '---', no libconfig '= { ... }', no TOML '[[...]]'",
            actual=f"yaml={has_yaml}, libconfig={has_libconfig}, toml={has_toml_table_array}",
            check_type="constraint",
        )
    )

    return details
