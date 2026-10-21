"""Behavioral checks for boot-uboot-003 (extlinux.conf)."""

import re

from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    body = generated_code

    # 1. default names a label that exists in the file.
    default_match = re.search(r"^default\s+(\S+)", body, re.MULTILINE)
    label_match = re.search(r"^label\s+(\S+)", body, re.MULTILINE)
    default_label = default_match.group(1) if default_match else ""
    label_name = label_match.group(1) if label_match else ""
    default_matches_label = bool(default_label) and default_label == label_name
    details.append(
        CheckDetail(
            check_name="default_matches_label",
            passed=default_matches_label,
            expected="default <name> matches an existing label <name>",
            actual=f"default={default_label!r}, label={label_name!r}",
            check_type="constraint",
        )
    )

    # 2. kernel path absolute under /boot.
    kernel_path = re.search(r"^\s*kernel\s+(/\S+)", body, re.MULTILINE)
    kernel_ok = bool(kernel_path) and kernel_path.group(1).startswith("/boot/")
    details.append(
        CheckDetail(
            check_name="kernel_path_absolute_under_boot",
            passed=kernel_ok,
            expected="kernel /boot/<image> absolute path",
            actual=kernel_path.group(1) if kernel_path else "missing",
            check_type="constraint",
        )
    )

    # 3. fdt path absolute under /boot.
    fdt_path = re.search(r"^\s*fdt\s+(/\S+)", body, re.MULTILINE)
    fdt_ok = bool(fdt_path) and fdt_path.group(1).startswith("/boot/")
    details.append(
        CheckDetail(
            check_name="fdt_path_absolute_under_boot",
            passed=fdt_ok,
            expected="fdt /boot/<dtb>",
            actual=fdt_path.group(1) if fdt_path else "missing",
            check_type="constraint",
        )
    )

    # 4. initrd path absolute under /boot.
    initrd_path = re.search(r"^\s*initrd\s+(/\S+)", body, re.MULTILINE)
    initrd_ok = bool(initrd_path) and initrd_path.group(1).startswith("/boot/")
    details.append(
        CheckDetail(
            check_name="initrd_path_absolute_under_boot",
            passed=initrd_ok,
            expected="initrd /boot/<cpio>",
            actual=initrd_path.group(1) if initrd_path else "missing",
            check_type="constraint",
        )
    )

    # 5. append has root= specifying the mmcblk1p2 partition.
    append_line = re.search(r"^\s*append\s+(.*)$", body, re.MULTILINE)
    append_text = append_line.group(1) if append_line else ""
    has_root = bool(re.search(r"root=/dev/mmcblk1p2\b", append_text))
    details.append(
        CheckDetail(
            check_name="append_root_mmcblk1p2",
            passed=has_root,
            expected="append root=/dev/mmcblk1p2",
            actual=f"append line: {append_text[:80]!r}",
            check_type="constraint",
        )
    )

    # 6. append has rootwait (handles late-probe SD).
    has_rootwait = "rootwait" in append_text
    details.append(
        CheckDetail(
            check_name="append_has_rootwait",
            passed=has_rootwait,
            expected="append includes rootwait (handles slow-enumerating SD)",
            actual="present" if has_rootwait else "missing",
            check_type="constraint",
        )
    )

    # 7. console=ttymxc1,115200 for i.MX8MP serial.
    has_console = bool(re.search(r"console=ttymxc\d+,\d+", append_text))
    details.append(
        CheckDetail(
            check_name="append_has_console_ttymxc",
            passed=has_console,
            expected="append console=ttymxc<N>,<baud>",
            actual=append_text[:80] if has_console else "missing",
            check_type="constraint",
        )
    )

    # 8. timeout is a positive integer.
    timeout_match = re.search(r"^timeout\s+(\d+)", body, re.MULTILINE)
    timeout_ok = bool(timeout_match) and int(timeout_match.group(1)) > 0
    details.append(
        CheckDetail(
            check_name="timeout_positive_integer",
            passed=timeout_ok,
            expected="timeout <positive integer>",
            actual=timeout_match.group(1) if timeout_match else "missing",
            check_type="constraint",
        )
    )

    return details
