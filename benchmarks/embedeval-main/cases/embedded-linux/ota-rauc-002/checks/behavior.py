"""Behavioral checks for ota-rauc-002 (A/B slot + hook)."""

import re

from embedeval.check_utils import (
    rauc_image_slots,
    rauc_manifest_section_has,
)
from embedeval.models import CheckDetail

_ALLOWED_BUNDLE_FORMATS = {"plain", "verity", "crypt"}
_SLOT_INDEX_RE = re.compile(r"^rootfs\.(\d+)$")


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. Two rootfs slots declared: image.rootfs.0 and image.rootfs.1.
    slots = rauc_image_slots(generated_code)
    rootfs_slots = [s for s in slots if _SLOT_INDEX_RE.match(s)]
    details.append(
        CheckDetail(
            check_name="two_rootfs_slots_declared",
            passed=len(rootfs_slots) == 2,
            expected="exactly 2 [image.rootfs.<N>] sections",
            actual=f"slots={slots}, indexed_rootfs={rootfs_slots}",
            check_type="constraint",
        )
    )

    # 2. Slot class naming uses numeric index (not a/b letters).
    indices = [m.group(1) for m in (_SLOT_INDEX_RE.match(s) for s in slots) if m]
    all_numeric = all(i.isdigit() for i in indices) and len(indices) == len(rootfs_slots)
    details.append(
        CheckDetail(
            check_name="slot_class_uses_numeric_index",
            passed=all_numeric and bool(indices),
            expected="image.rootfs.<N> with integer N (not a/b letters)",
            actual=f"indices={indices}",
            check_type="constraint",
        )
    )

    # 3. Slot filenames distinct (A ≠ B bytes).
    fn0 = rauc_manifest_section_has(generated_code, "image.rootfs.0", "filename")
    fn1 = rauc_manifest_section_has(generated_code, "image.rootfs.1", "filename")
    filenames_distinct = bool(fn0) and bool(fn1) and fn0 != fn1
    details.append(
        CheckDetail(
            check_name="slot_filenames_distinct",
            passed=filenames_distinct,
            expected="image.rootfs.0 filename ≠ image.rootfs.1 filename",
            actual=f"0={fn0!r}, 1={fn1!r}",
            check_type="constraint",
        )
    )

    # 4. Slot sha256 values distinct.
    sha0 = rauc_manifest_section_has(generated_code, "image.rootfs.0", "sha256")
    sha1 = rauc_manifest_section_has(generated_code, "image.rootfs.1", "sha256")
    sha_distinct = bool(sha0) and bool(sha1) and sha0 != sha1
    details.append(
        CheckDetail(
            check_name="slot_sha256_distinct",
            passed=sha_distinct,
            expected="image.rootfs.0 sha256 ≠ image.rootfs.1 sha256",
            actual=f"0={sha0!r}, 1={sha1!r}",
            check_type="constraint",
        )
    )

    # 5. Every rootfs slot has filename / sha256 / size.
    all_have_filename = all(
        rauc_manifest_section_has(generated_code, f"image.{s}", "filename")
        for s in rootfs_slots
    ) and bool(rootfs_slots)
    all_have_sha = all(
        rauc_manifest_section_has(generated_code, f"image.{s}", "sha256")
        for s in rootfs_slots
    ) and bool(rootfs_slots)
    all_have_size = all(
        rauc_manifest_section_has(generated_code, f"image.{s}", "size")
        for s in rootfs_slots
    ) and bool(rootfs_slots)
    details.append(
        CheckDetail(
            check_name="every_slot_has_filename",
            passed=all_have_filename,
            expected="every rootfs slot has filename=",
            actual=f"slots={rootfs_slots}",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="every_slot_has_sha256",
            passed=all_have_sha,
            expected="every rootfs slot has sha256=",
            actual=f"slots={rootfs_slots}",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="every_slot_has_size",
            passed=all_have_size,
            expected="every rootfs slot has size=",
            actual=f"slots={rootfs_slots}",
            check_type="constraint",
        )
    )

    # 6. [hooks] section registers a filename (install-check hook).
    hook_fn = rauc_manifest_section_has(generated_code, "hooks", "filename")
    details.append(
        CheckDetail(
            check_name="hooks_has_filename",
            passed=bool(hook_fn),
            expected="[hooks] filename=<hook-script>",
            actual=f"{hook_fn!r}" if hook_fn else "missing",
            check_type="constraint",
        )
    )

    # 7. Update compatible uses vendor,product convention.
    compatible = rauc_manifest_section_has(generated_code, "update", "compatible")
    details.append(
        CheckDetail(
            check_name="update_has_compatible",
            passed=bool(compatible),
            expected="[update] compatible=<vendor,product>",
            actual=f"{compatible!r}" if compatible else "missing",
            check_type="constraint",
        )
    )

    # 8. [bundle] format valid.
    fmt = rauc_manifest_section_has(generated_code, "bundle", "format")
    details.append(
        CheckDetail(
            check_name="bundle_format_valid",
            passed=bool(fmt) and fmt in _ALLOWED_BUNDLE_FORMATS,
            expected=f"format in {sorted(_ALLOWED_BUNDLE_FORMATS)}",
            actual=f"{fmt!r}",
            check_type="constraint",
        )
    )

    # 9. No single-slot collapse (exactly-one rootfs slot would defeat A/B).
    details.append(
        CheckDetail(
            check_name="no_single_slot_collapse",
            passed=len(rootfs_slots) >= 2,
            expected="≥2 rootfs slots (A/B requires two)",
            actual=f"{len(rootfs_slots)} rootfs slots",
            check_type="constraint",
        )
    )

    # 10. Atomic switchover is IMPLIED by two distinct slots — no
    # ``inplace=true`` flag hinting in-place overwrite (RAUC does not
    # support in-place; a stray ``inplace`` directive would indicate
    # the LLM hallucinated a foreign option).
    has_inplace = bool(
        re.search(r"^\s*inplace\s*=", generated_code, re.MULTILINE | re.IGNORECASE)
    )
    details.append(
        CheckDetail(
            check_name="no_inplace_directive",
            passed=not has_inplace,
            expected="no inplace= directive",
            actual="detected" if has_inplace else "clean",
            check_type="constraint",
        )
    )

    return details
