"""Behavioral checks for boot-uboot-002 (FIT image .its)."""

import re

from embedeval.check_utils import scoped_contains, strip_comments
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    body = strip_comments(generated_code)

    # 1. Kernel sub-image has load and entry addresses.
    kernel_region = re.search(
        r'type\s*=\s*"kernel"[^}]*?hash', body, re.DOTALL
    )
    kernel_text = kernel_region.group(0) if kernel_region else ""
    has_load = "load" in kernel_text and "=" in kernel_text
    has_entry = "entry" in kernel_text and "=" in kernel_text
    details.append(
        CheckDetail(
            check_name="kernel_load_and_entry_addresses",
            passed=has_load and has_entry,
            expected="kernel sub-image has load = <..> and entry = <..>",
            actual=f"load={has_load}, entry={has_entry}",
            check_type="constraint",
        )
    )

    # 2. arch = "arm64" set on kernel.
    arm64_in_kernel = bool(
        re.search(
            r'type\s*=\s*"kernel"[^}]*arch\s*=\s*"arm64"', body, re.DOTALL
        )
    )
    details.append(
        CheckDetail(
            check_name="kernel_arch_arm64",
            passed=arm64_in_kernel,
            expected='kernel sub-image declares arch = "arm64"',
            actual="present" if arm64_in_kernel else "missing or wrong",
            check_type="constraint",
        )
    )

    # 3. os = "linux" on kernel.
    kernel_os_linux = bool(
        re.search(
            r'type\s*=\s*"kernel"[^}]*os\s*=\s*"linux"', body, re.DOTALL
        )
    )
    details.append(
        CheckDetail(
            check_name="kernel_os_linux",
            passed=kernel_os_linux,
            expected='kernel sub-image declares os = "linux"',
            actual="present" if kernel_os_linux else "missing",
            check_type="constraint",
        )
    )

    # 4. Every sub-image has a hash sub-node with sha256.
    # Count hash nodes with algo = "sha256".
    sha256_nodes = len(re.findall(r'algo\s*=\s*"sha256"', body))
    details.append(
        CheckDetail(
            check_name="hash_sha256_on_every_subimage",
            passed=sha256_nodes >= 3,
            expected='at least 3 hash nodes with algo = "sha256" (kernel + fdt + ramdisk)',
            actual=f"found {sha256_nodes} sha256 hash nodes",
            check_type="constraint",
        )
    )

    # 5. configurations { config-1 { kernel=...; fdt=...; ramdisk=...; } }.
    config_block = re.search(r"config-1\s*\{([^}]*)\}", body, re.DOTALL)
    config_text = config_block.group(1) if config_block else ""
    has_kernel_ref = bool(re.search(r"kernel\s*=\s*\"kernel", config_text))
    has_fdt_ref = bool(re.search(r"fdt\s*=\s*\"fdt", config_text))
    has_ramdisk_ref = bool(re.search(r"ramdisk\s*=\s*\"ramdisk", config_text))
    details.append(
        CheckDetail(
            check_name="config1_references_all_three_images",
            passed=has_kernel_ref and has_fdt_ref and has_ramdisk_ref,
            expected="config-1 references kernel + fdt + ramdisk sub-images",
            actual=f"kernel={has_kernel_ref}, fdt={has_fdt_ref}, ramdisk={has_ramdisk_ref}",
            check_type="constraint",
        )
    )

    # 6. /incbin/ directive used for data payloads (standard mkimage
    # inclusion syntax).
    has_incbin = "/incbin/" in body
    details.append(
        CheckDetail(
            check_name="incbin_directive_used",
            passed=has_incbin,
            expected="/incbin/ directive used for sub-image data payloads",
            actual="present" if has_incbin else "missing",
            check_type="constraint",
        )
    )

    # 7. Compression attribute on kernel AND ramdisk (even if "none" or "gzip").
    kernel_has_compression = bool(
        re.search(
            r'type\s*=\s*"kernel"[^}]*compression\s*=', body, re.DOTALL
        )
    )
    ramdisk_has_compression = bool(
        re.search(
            r'type\s*=\s*"ramdisk"[^}]*compression\s*=', body, re.DOTALL
        )
    )
    details.append(
        CheckDetail(
            check_name="kernel_and_ramdisk_have_compression",
            passed=kernel_has_compression and ramdisk_has_compression,
            expected="compression property on kernel and ramdisk sub-images",
            actual=f"kernel={kernel_has_compression}, ramdisk={ramdisk_has_compression}",
            check_type="constraint",
        )
    )

    # 8. Default points to an existing config (config-1).
    default_matches = scoped_contains(
        generated_code, 'default = "config-1"', scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="default_points_to_config1",
            passed=default_matches,
            expected='configurations { default = "config-1"; ... }',
            actual="present" if default_matches else "missing or points elsewhere",
            check_type="constraint",
        )
    )

    return details
