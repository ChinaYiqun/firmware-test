"""Negative tests for boot-uboot-003 (extlinux.conf)."""

import re


def _drop_default_line(code: str) -> str:
    return re.sub(r"^default\s+\S+\s*\n", "", code, count=1, flags=re.MULTILINE)


def _default_points_to_nonexistent_label(code: str) -> str:
    return code.replace("default linux", "default rescue")


def _drop_timeout(code: str) -> str:
    return re.sub(r"^timeout\s+\d+\s*\n", "", code, count=1, flags=re.MULTILINE)


def _timeout_zero(code: str) -> str:
    return code.replace("timeout 10", "timeout 0")


def _kernel_relative_path(code: str) -> str:
    return code.replace("kernel /boot/Image", "kernel Image")


def _fdt_relative_path(code: str) -> str:
    return code.replace("fdt /boot/imx8mp.dtb", "fdt imx8mp.dtb")


def _initrd_relative_path(code: str) -> str:
    return code.replace(
        "initrd /boot/initramfs.cpio.gz", "initrd initramfs.cpio.gz"
    )


def _drop_root_cmdline(code: str) -> str:
    return code.replace("root=/dev/mmcblk1p2 ", "")


def _drop_rootwait(code: str) -> str:
    return code.replace("rootwait ", "")


def _drop_console(code: str) -> str:
    return code.replace(" console=ttymxc1,115200", "")


def _drop_label_line(code: str) -> str:
    return re.sub(r"^label\s+\S+\s*\n", "", code, count=1, flags=re.MULTILINE)


def _swap_root_to_wrong_partition(code: str) -> str:
    return code.replace("root=/dev/mmcblk1p2", "root=/dev/mmcblk0p1")


NEGATIVES = [
    {
        "name": "drop_default",
        "description": "Remove default directive — U-Boot cannot know which label to auto-boot.",
        "mutation": _drop_default_line,
        "must_fail": ["default_directive_present", "default_matches_label"],
        "factor_id": "F6.1",
    },
    {
        "name": "default_points_to_nonexistent_label",
        "description": 'default rescue but no rescue label — u-boot extlinux reports missing label.',
        "mutation": _default_points_to_nonexistent_label,
        "must_fail": ["default_matches_label"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_timeout",
        "description": "Remove timeout — boots default immediately; fine for some but required by the prompt.",
        "mutation": _drop_timeout,
        "must_fail": ["timeout_directive_present", "timeout_positive_integer"],
        "factor_id": "F6.1",
    },
    {
        "name": "timeout_zero",
        "description": "timeout 0 — skip the boot menu entirely, prompt explicitly asked for a low but positive timeout.",
        "mutation": _timeout_zero,
        "must_fail": ["timeout_positive_integer"],
        "factor_id": "F6.2",
    },
    {
        "name": "kernel_relative_path",
        "description": "kernel Image (relative) — U-Boot extlinux expects absolute paths on the boot media.",
        "mutation": _kernel_relative_path,
        "must_fail": ["kernel_path_absolute_under_boot"],
        "factor_id": "F6.2",
    },
    {
        "name": "fdt_relative_path",
        "description": "fdt imx8mp.dtb (relative) — DT blob not found.",
        "mutation": _fdt_relative_path,
        "must_fail": ["fdt_path_absolute_under_boot"],
        "factor_id": "F6.2",
    },
    {
        "name": "initrd_relative_path",
        "description": "initrd initramfs.cpio.gz (relative) — initramfs not found.",
        "mutation": _initrd_relative_path,
        "must_fail": ["initrd_path_absolute_under_boot"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_root_cmdline",
        "description": "Remove root= from append — kernel panics, no root filesystem.",
        "mutation": _drop_root_cmdline,
        "must_fail": ["append_root_mmcblk1p2"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_rootwait",
        "description": "Remove rootwait — kernel may race SD enumeration and fail to find root.",
        "mutation": _drop_rootwait,
        "must_fail": ["append_has_rootwait"],
        "factor_id": "B3.2",
    },
    {
        "name": "drop_console",
        "description": "Remove console= — no serial console; debug output invisible.",
        "mutation": _drop_console,
        "must_fail": ["append_has_console_ttymxc"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_label",
        "description": "Remove the label block entirely — nothing to boot.",
        "mutation": _drop_label_line,
        "must_fail": ["label_directive_present", "default_matches_label"],
        "factor_id": "F6.1",
    },
    {
        "name": "wrong_root_partition",
        "description": "root=/dev/mmcblk0p1 — wrong partition (and typically boot partition, not rootfs).",
        "mutation": _swap_root_to_wrong_partition,
        "must_fail": ["append_root_mmcblk1p2"],
        "factor_id": "A1.1",
    },
]
