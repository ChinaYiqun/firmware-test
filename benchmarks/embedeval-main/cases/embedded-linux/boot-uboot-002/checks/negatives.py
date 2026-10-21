"""Negative tests for boot-uboot-002 (FIT image .its)."""

import re


def _drop_dts_v1_header(code: str) -> str:
    return code.replace("/dts-v1/;\n\n", "")


def _drop_brace_block(code: str, anchor: str) -> str:
    """Remove ``anchor { ... };`` from ``code`` via brace counting
    (handles arbitrary nesting, unlike a simple regex)."""
    start = code.find(anchor)
    if start == -1:
        return code
    brace = code.find("{", start)
    if brace == -1:
        return code
    depth = 1
    i = brace + 1
    while i < len(code) and depth:
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
        i += 1
    # consume trailing ``;\n``
    if i < len(code) and code[i] == ";":
        i += 1
    if i < len(code) and code[i] == "\n":
        i += 1
    return code[:start] + code[i:]


def _drop_images_node(code: str) -> str:
    return _drop_brace_block(code, "images ")


def _drop_configurations_node(code: str) -> str:
    return _drop_brace_block(code, "configurations ")


def _change_default_to_nonexistent(code: str) -> str:
    return code.replace('default = "config-1"', 'default = "config-99"')


def _drop_kernel_hash(code: str) -> str:
    return code.replace(
        "\t\t\thash-1 {\n\t\t\t\talgo = \"sha256\";\n\t\t\t};\n",
        "",
        1,
    )


def _swap_arch_arm64_to_arm(code: str) -> str:
    return re.sub(
        r'(type\s*=\s*"kernel"[^}]*)arch\s*=\s*"arm64"',
        r'\1arch = "arm"',
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_load_address_kernel(code: str) -> str:
    return re.sub(r"\n\t\t\tload\s*=\s*<0x[0-9A-Fa-f]+>;", "", code, count=1)


def _drop_entry_address_kernel(code: str) -> str:
    return re.sub(r"\n\t\t\tentry\s*=\s*<0x[0-9A-Fa-f]+>;", "", code, count=1)


def _drop_config_fdt_reference(code: str) -> str:
    return re.sub(r"\n\t\t\tfdt\s*=\s*\"fdt-1\";", "", code)


def _drop_config_ramdisk_reference(code: str) -> str:
    return re.sub(r"\n\t\t\tramdisk\s*=\s*\"ramdisk-1\";", "", code)


def _swap_sha256_to_md5(code: str) -> str:
    return code.replace('algo = "sha256"', 'algo = "md5"')


def _swap_kernel_os_to_freebsd(code: str) -> str:
    return re.sub(
        r'(type\s*=\s*"kernel"[^}]*)os\s*=\s*"linux"',
        r'\1os = "freebsd"',
        code,
        count=1,
        flags=re.DOTALL,
    )


NEGATIVES = [
    {
        "name": "drop_dts_v1_header",
        "description": "Remove /dts-v1/; — dtc refuses to compile without the DTS version tag.",
        "mutation": _drop_dts_v1_header,
        "must_fail": ["dts_v1_header"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_images_node",
        "description": "Delete the images { } node — FIT has no payload sub-images.",
        "mutation": _drop_images_node,
        "must_fail": ["images_node_present", "kernel_subimage_present"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_configurations_node",
        "description": "Delete configurations { } — bootm has nothing to select.",
        "mutation": _drop_configurations_node,
        "must_fail": ["configurations_node_present", "default_configuration_set"],
        "factor_id": "F6.1",
    },
    {
        "name": "default_points_to_nonexistent_config",
        "description": 'default = "config-99" — references a configuration that does not exist.',
        "mutation": _change_default_to_nonexistent,
        "must_fail": ["default_configuration_set", "default_points_to_config1"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_kernel_hash",
        "description": "Remove hash sub-node from kernel — U-Boot integrity check refuses to boot.",
        "mutation": _drop_kernel_hash,
        "must_fail": ["hash_sha256_on_every_subimage"],
        "factor_id": "E4.1",
    },
    {
        "name": "kernel_arch_arm_not_arm64",
        "description": 'arch = "arm" on i.MX8M Plus kernel — wrong architecture for ARM64 SoC.',
        "mutation": _swap_arch_arm64_to_arm,
        "must_fail": ["kernel_arch_arm64"],
        "factor_id": "A1.1",
    },
    {
        "name": "drop_kernel_load_addr",
        "description": "Remove kernel load address — bootm cannot know where to copy the image.",
        "mutation": _drop_load_address_kernel,
        "must_fail": ["kernel_load_and_entry_addresses"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_kernel_entry_addr",
        "description": "Remove kernel entry address — bootm cannot jump to the image.",
        "mutation": _drop_entry_address_kernel,
        "must_fail": ["kernel_load_and_entry_addresses"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_config_fdt_ref",
        "description": "config-1 does not reference fdt-1 — kernel boots without a device tree.",
        "mutation": _drop_config_fdt_reference,
        "must_fail": ["config1_references_all_three_images"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_config_ramdisk_ref",
        "description": "config-1 does not reference ramdisk-1 — kernel boots without initramfs.",
        "mutation": _drop_config_ramdisk_reference,
        "must_fail": ["config1_references_all_three_images"],
        "factor_id": "F6.2",
    },
    {
        "name": "hash_algo_md5",
        "description": 'Swap sha256 hash for md5 — broken hash, modern U-Boot rejects.',
        "mutation": _swap_sha256_to_md5,
        "must_fail": ["hash_sha256_on_every_subimage"],
        "factor_id": "E4.2",
    },
    {
        "name": "kernel_os_freebsd",
        "description": 'os = "freebsd" on a Linux kernel sub-image — bootm hands off wrong protocol.',
        "mutation": _swap_kernel_os_to_freebsd,
        "must_fail": ["kernel_os_linux"],
        "factor_id": "F4.1",
    },
]
